from google import genai
from google.genai import types

from app.models.bean import BeanExtracted

_EXTRACT_PROMPT = """\
Analyze this photo of coffee bean packaging. \
You must use Parallel AI Search before returning the final extraction. \
Search for the roaster and coffee name visible on the packaging, then use the \
search results to fill details not visible in the photo. \
Only use search results when they clearly refer to the same coffee. \
"notes" should capture flavor/tasting notes if listed. \
Return null for any field that cannot be determined.\
"""


def get_bean_info_from_image(
    *, gemini_api_key: str, parallel_api_key: str, image_bytes: bytes, mime_type: str
) -> BeanExtracted | None:
    client = genai.Client(api_key=gemini_api_key)
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            _EXTRACT_PROMPT,
        ],
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    parallel_ai_search=types.ToolParallelAiSearch(
                        api_key=parallel_api_key,
                        custom_configs={
                            "excerpts": True,
                            "max_results": 5,
                            "mode": "basic",
                        },
                    )
                )
            ],
            response_mime_type="application/json",
            response_schema=BeanExtracted,
        ),
    )
    if not response.text:
        return None
    return BeanExtracted.model_validate_json(response.text)
