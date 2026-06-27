from dataclasses import dataclass
from textwrap import dedent
from typing import Any

from parallel import AsyncParallel
from pydantic_ai import Agent, BinaryContent, ModelRetry, RunContext, UsageLimits
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app.lib.countries import country_candidates
from app.lib.normalization import validate_entity_resolution
from app.models.bean import BeanExtracted, CanonicalSelection
from app.models.entities import NormalizationCandidate, NormalizationKind
from app.storage.entities import EntityStorage

_EXTRACT_PROMPT = dedent(
    """
    Analyze this photo of coffee bean packaging. You must call the parallel_search tool
    before returning the final extraction. Search for the roaster and coffee name visible
    on the packaging. After receiving search results, extract visible information from the
    photo and use the search results to fill details not visible in the photo. Only use
    search results when they clearly refer to the same coffee. "notes" should capture
    flavor/tasting notes if listed.

    For any roaster, producer, farm, variety, process, or country value you find, call
    find_normalization_candidates with the raw value and matching kind before returning.
    If an existing candidate is the same real-world entity, return it as
    {"resolution":"matched","canonical_id":candidate.id,"name":candidate.canonical_name}.
    Only return {"resolution":"proposed","canonical_id":null,"name":raw_name} when no
    candidate represents the same entity.

    A country candidate ID is its ISO country code; other candidate IDs are database UUIDs.
    Never invent a canonical ID. Countries must always be matched to the ISO candidates or
    returned as null; never propose a country. Return null for any field that cannot be
    determined.
    """
).strip()
_GEMINI_MODEL = "gemini-3.1-flash-lite"


@dataclass
class BeanPhotoDeps:
    parallel_api_key: str
    entity_storage: EntityStorage
    searched: bool = False
    normalization_candidates: dict[NormalizationKind, dict[str, str]] | None = None


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


@_bean_photo_agent.tool
async def find_normalization_candidates(
    ctx: RunContext[BeanPhotoDeps],
    kind: NormalizationKind,
    value: str,
    limit: int = 8,
) -> list[NormalizationCandidate]:
    """Find canonical entity candidates for raw coffee metadata text."""
    if kind == "country":
        candidates = [
            NormalizationCandidate(
                id=candidate.code,
                kind="country",
                canonical_name=candidate.name,
                aliases=[],
                score=candidate.score,
                match_reason="country_match",
            )
            for candidate in country_candidates(value, limit=limit)
        ]
    else:
        candidates = ctx.deps.entity_storage.candidates(kind=kind, value=value, limit=limit)
    if ctx.deps.normalization_candidates is None:
        ctx.deps.normalization_candidates = {}
    ctx.deps.normalization_candidates[kind] = {
        candidate.id: candidate.canonical_name for candidate in candidates
    }
    return candidates


@_bean_photo_agent.output_validator
def require_parallel_search(ctx: RunContext[BeanPhotoDeps], output: BeanExtracted) -> BeanExtracted:
    if not ctx.deps.searched:
        raise ModelRetry("You must call parallel_search before returning the extraction.")
    entity_fields: list[tuple[NormalizationKind, CanonicalSelection | None]] = [
        ("roaster", output.roaster),
        ("producer", output.producer),
        ("farm", output.farm),
        ("country", output.country),
        ("variety", output.variety),
        ("process", output.process),
    ]
    for kind, value in entity_fields:
        if not value:
            continue
        validate_entity_resolution(kind, value, ctx.deps.normalization_candidates)
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
