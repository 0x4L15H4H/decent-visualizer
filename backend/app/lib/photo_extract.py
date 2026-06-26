from dataclasses import dataclass
from typing import Any

from parallel import AsyncParallel
from pydantic_ai import Agent, BinaryContent, ModelRetry, RunContext, UsageLimits
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app.models.bean import BeanExtracted
from app.models.entities import NormalizationCandidate
from app.storage.entities import EntityStorage

_EXTRACT_PROMPT = (
    "Analyze this photo of coffee bean packaging. You must call the parallel_search tool "
    "before returning the final extraction. Search for the roaster and coffee name visible "
    "on the packaging. After receiving search results, extract visible information from the "
    "photo and use the search results to fill details not visible in the photo. Only use "
    'search results when they clearly refer to the same coffee. "notes" should capture '
    "flavor/tasting notes if listed. If you find a processing method, call "
    "find_process_candidates with the raw process text before returning. When candidates "
    "are returned, set process to exactly one candidate canonical_name. If no candidate "
    "clearly matches, set process to null. Return null for any field that cannot be "
    "determined."
)
_GEMINI_MODEL = "gemini-3.1-flash-lite"


@dataclass
class BeanPhotoDeps:
    parallel_api_key: str
    entity_storage: EntityStorage
    searched: bool = False
    process_candidate_names: set[str] | None = None


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
async def find_process_candidates(
    ctx: RunContext[BeanPhotoDeps],
    value: str,
    limit: int = 8,
) -> list[NormalizationCandidate]:
    """Find canonical process candidates for raw coffee processing text."""
    candidates = ctx.deps.entity_storage.candidates(kind="process", value=value, limit=limit)
    ctx.deps.process_candidate_names = {candidate.canonical_name for candidate in candidates}
    return candidates


@_bean_photo_agent.output_validator
def require_parallel_search(ctx: RunContext[BeanPhotoDeps], output: BeanExtracted) -> BeanExtracted:
    if not ctx.deps.searched:
        raise ModelRetry("You must call parallel_search before returning the extraction.")
    if output.process and ctx.deps.process_candidate_names is None:
        raise ModelRetry("Call find_process_candidates before returning a process.")
    if (
        output.process
        and ctx.deps.process_candidate_names
        and output.process not in ctx.deps.process_candidate_names
    ):
        raise ModelRetry("Set process to exactly one returned process candidate canonical_name.")
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
        usage_limits=UsageLimits(request_limit=5, tool_calls_limit=3),
    )
    return result.output
