from typing import Any, cast

from google import genai
from google.genai import types
from parallel import Parallel

from app.models.bean import BeanExtracted

_EXTRACT_PROMPT = """\
Analyze this photo of coffee bean packaging. \
You must call the parallel_search tool before returning the final extraction. \
Search for the roaster and coffee name visible on the packaging. \
After receiving search results, extract visible information from the photo and \
use the search results to fill details not visible in the photo. \
Only use search results when they clearly refer to the same coffee. \
"notes" should capture flavor/tasting notes if listed. \
Return null for any field that cannot be determined.\
"""

_PARALLEL_SEARCH = "parallel_search"
_MAX_FUNCTION_CALLS = 3


def _parallel_search_tool() -> types.Tool:
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name=_PARALLEL_SEARCH,
                description=(
                    "Search the web with Parallel AI Search for exact coffee bean details. "
                    "Use packaging-visible roaster and coffee names in the query."
                ),
                parameters_json_schema={
                    "type": "object",
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "One to three focused web search queries for this exact coffee."
                            ),
                            "minItems": 1,
                            "maxItems": 3,
                        },
                        "objective": {
                            "type": "string",
                            "description": (
                                "What coffee details to retrieve, such as roaster, producer, "
                                "farm, country, variety, process, and tasting notes."
                            ),
                        },
                    },
                    "required": ["queries"],
                },
            )
        ]
    )


def _parallel_search(*, api_key: str, args: dict[str, object]) -> dict[str, Any]:
    raw_queries = args.get("queries")
    search_queries: list[str] = []
    if isinstance(raw_queries, list):
        for query in cast("list[object]", raw_queries):
            if isinstance(query, str) and query.strip():
                search_queries.append(query)
            if len(search_queries) == 3:
                break
    if not search_queries:
        return {"error": "parallel_search requires at least one non-empty query."}

    objective = args.get("objective")
    if not isinstance(objective, str) or not objective.strip():
        objective = (
            "Find exact coffee bean details including roaster, producer, farm, country, "
            "variety, process, and tasting notes where available."
        )

    search = Parallel(api_key=api_key).search(
        search_queries=search_queries,
        objective=objective,
        mode="basic",
        max_chars_total=5000,
    )
    return search.model_dump(mode="json")


def _function_calls(response: types.GenerateContentResponse) -> list[types.FunctionCall]:
    calls: list[types.FunctionCall] = []
    for candidate in response.candidates or []:
        if not candidate.content:
            continue
        for part in candidate.content.parts or []:
            if part.function_call:
                calls.append(part.function_call)
    return calls


def get_bean_info_from_image(
    *, gemini_api_key: str, parallel_api_key: str, image_bytes: bytes, mime_type: str
) -> BeanExtracted | None:
    client = genai.Client(api_key=gemini_api_key)
    contents: list[types.Content] = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part(text=_EXTRACT_PROMPT),
            ],
        )
    ]
    tool_config = types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(
            mode=types.FunctionCallingConfigMode.ANY,
            allowed_function_names=[_PARALLEL_SEARCH],
        )
    )

    for _ in range(_MAX_FUNCTION_CALLS):
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                tools=[_parallel_search_tool()],
                tool_config=tool_config,
            ),
        )
        calls = _function_calls(response)
        if not calls:
            break

        model_content = next(
            (
                candidate.content
                for candidate in response.candidates or []
                if candidate.content and candidate.content.parts
            ),
            None,
        )
        if model_content is None:
            break
        contents.append(model_content)
        response_parts: list[types.Part] = []
        for call in calls:
            response_parts.append(
                types.Part.from_function_response(
                    name=call.name or _PARALLEL_SEARCH,
                    response=_parallel_search(
                        api_key=parallel_api_key,
                        args=call.args or {},
                    ),
                )
            )
        contents.append(types.Content(role="tool", parts=response_parts))

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BeanExtracted,
        ),
    )
    if not response.text:
        return None
    return BeanExtracted.model_validate_json(response.text)
