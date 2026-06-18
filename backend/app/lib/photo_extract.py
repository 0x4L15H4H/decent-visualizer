from google import genai
from google.genai import types

from app.models.bean import BeanExtracted

_EXTRACT_PROMPT = """\
Analyze this photo of coffee bean packaging. \
Extract any visible information. \
"notes" should capture flavor/tasting notes if listed. \
Use Google Search to look up the roaster or coffee name \
for any details not visible in the photo. \
Return null for any field that cannot be determined.\
"""


def get_bean_info_from_image(
    *, api_key: str, image_bytes: bytes, mime_type: str
) -> BeanExtracted | None:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            _EXTRACT_PROMPT,
        ],
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            response_mime_type="application/json",
            response_schema=BeanExtracted,
        ),
    )
    if not response.text:
        return None
    return BeanExtracted.model_validate_json(response.text)
