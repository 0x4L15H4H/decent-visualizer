from dataclasses import dataclass
from typing import Any

from parallel import AsyncParallel
from pydantic_ai import Agent, BinaryContent, ModelRetry, RunContext, UsageLimits
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app.lib.countries import CountryCandidate, country_candidates
from app.models.bean import BeanExtracted
from app.models.entities import EntityKind, NormalizationCandidate
from app.storage.entities import EntityStorage

_EXTRACT_PROMPT = (
    "Analyze this photo of coffee bean packaging. You must call the parallel_search tool "
    "before returning the final extraction. Search for the roaster and coffee name visible "
    "on the packaging. After receiving search results, extract visible information from the "
    "photo and use the search results to fill details not visible in the photo. Only use "
    'search results when they clearly refer to the same coffee. "notes" should capture '
    "flavor/tasting notes if listed. For any roaster, producer, farm, variety, or process "
    "value you find, call find_normalization_candidates with the raw value and matching "
    "kind before returning. When candidates are returned, use an exact candidate "
    "canonical_name if it clearly matches; otherwise keep the raw value. For any country "
    "value you find, call normalize_country before returning and set country to the exact "
    "returned country name if one clearly matches. Return null for any field that cannot "
    "be determined."
)
_GEMINI_MODEL = "gemini-3.1-flash-lite"


@dataclass
class BeanPhotoDeps:
    parallel_api_key: str
    entity_storage: EntityStorage
    searched: bool = False
    entity_candidate_names: dict[EntityKind, set[str]] | None = None
    country_candidate_names: set[str] | None = None


_bean_photo_agent = Agent[BeanPhotoDeps, BeanExtracted](
    deps_type=BeanPhotoDeps,
    output_type=BeanExtracted,
    instructions=_EXTRACT_PROMPT,
    retries=2,
)


@_bean_photo_agent.tool
async def parallel_search(
    ctx: RunContext[BeanPhotoDeps],
    queries: list[str],
    objective: str | None = None,
) -> dict[str, Any]:
    """Search the web for exact coffee bean details visible or implied by the packaging."""
    search_queries = [query for query in queries[:3] if query.strip()]
    if not search_queries:
        raise ModelRetry("Provide at least one non-empty query.")

    if not objective:
        objective = (
            "Find exact coffee bean details including roaster, producer, farm, country, "
            "variety, process, and tasting notes where available."
        )

    ctx.deps.searched = True
    async with AsyncParallel(api_key=ctx.deps.parallel_api_key) as parallel:
        search = await parallel.search(
            search_queries=search_queries,
            objective=objective,
            mode="basic",
            max_chars_total=5000,
        )
    return search.model_dump(mode="json")


def _candidate_names(deps: BeanPhotoDeps) -> dict[EntityKind, set[str]]:
    if deps.entity_candidate_names is None:
        deps.entity_candidate_names = {}
    return deps.entity_candidate_names


@_bean_photo_agent.tool
async def find_normalization_candidates(
    ctx: RunContext[BeanPhotoDeps],
    kind: EntityKind,
    value: str,
    limit: int = 8,
) -> list[NormalizationCandidate]:
    """Find canonical entity candidates for raw coffee metadata text."""
    candidates = ctx.deps.entity_storage.candidates(kind=kind, value=value, limit=limit)
    _candidate_names(ctx.deps)[kind] = {candidate.canonical_name for candidate in candidates}
    return candidates


@_bean_photo_agent.tool
async def normalize_country(
    ctx: RunContext[BeanPhotoDeps],
    value: str,
    limit: int = 8,
) -> list[CountryCandidate]:
    """Find canonical country candidates for raw country or origin text."""
    candidates = country_candidates(value, limit=limit)
    ctx.deps.country_candidate_names = {candidate.name for candidate in candidates}
    return candidates


@_bean_photo_agent.output_validator
def require_parallel_search(ctx: RunContext[BeanPhotoDeps], output: BeanExtracted) -> BeanExtracted:
    if not ctx.deps.searched:
        raise ModelRetry("You must call parallel_search before returning the extraction.")
    entity_fields: list[tuple[EntityKind, str | None]] = [
        ("roaster", output.roaster),
        ("producer", output.producer),
        ("farm", output.farm),
        ("variety", output.variety),
        ("process", output.process),
    ]
    for kind, value in entity_fields:
        if not value:
            continue
        candidate_names = (ctx.deps.entity_candidate_names or {}).get(kind)
        if candidate_names is None:
            raise ModelRetry(f"Call find_normalization_candidates before returning {kind}.")
        if candidate_names and value not in candidate_names:
            raise ModelRetry(f"Set {kind} to exactly one returned candidate canonical_name.")
    if output.country and ctx.deps.country_candidate_names is None:
        raise ModelRetry("Call normalize_country before returning country.")
    if (
        output.country
        and ctx.deps.country_candidate_names
        and output.country not in ctx.deps.country_candidate_names
    ):
        raise ModelRetry("Set country to exactly one returned country name.")
    return output


async def get_bean_info_from_image(
    *,
    gemini_api_key: str,
    parallel_api_key: str,
    entity_storage: EntityStorage,
    image_bytes: bytes,
    mime_type: str,
) -> BeanExtracted | None:
    deps = BeanPhotoDeps(parallel_api_key=parallel_api_key, entity_storage=entity_storage)
    model = GoogleModel(
        _GEMINI_MODEL,
        provider=GoogleProvider(api_key=gemini_api_key),
    )
    result = await _bean_photo_agent.run(
        [
            "Extract coffee bean information from this package photo.",
            BinaryContent(data=image_bytes, media_type=mime_type),
        ],
        deps=deps,
        model=model,
        usage_limits=UsageLimits(request_limit=8, tool_calls_limit=10),
    )
    return result.output
