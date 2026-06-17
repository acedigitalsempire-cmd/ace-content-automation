import google.genai as genai
import json
import os
from config import GEMINI_API_KEY, BRAND_NAME, BRAND_NICHE, BRAND_AUDIENCE

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_topic_and_script():
    prompt = f"""
    You are a content strategist for {BRAND_NAME}, a digital marketing agency.
    Target audience: Nigerian entrepreneurs and SME owners aged 18-35.
    Niche: {BRAND_NICHE}

    Generate a short educational video topic and script.

    Return ONLY this JSON format, nothing else, no markdown, no backticks:
    {{
        "topic": "video topic here",
        "caption": "engaging social media caption with relevant hashtags",
        "scenes": [
            {{
                "text": "text to show on screen max 10 words",
                "voiceover": "what the narrator says max 30 words",
                "image_prompt": "detailed prompt to generate relevant image"
            }}
        ]
    }}

    Rules:
    - Maximum 5 scenes
    - Each voiceover max 30 words
    - Educational and valuable content
    - Focus on AI tools, digital marketing, or tech for business
    - Caption must include 5 relevant hashtags
    - Return pure JSON only
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    text = response.text.strip()

    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    return json.loads(text)


def generate_image(prompt, index):
    from PIL import Image
    import io
    import base64

    image_prompt = f"{prompt}, professional, clean, modern, tech style, no text"

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=image_prompt,
        config=genai.types.GenerateContentConfig(
            response_modalities=["image", "text"]
        )
    )

    image_path = f"/tmp/scene_{index}.png"

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_data = base64.b64decode(part.inline_data.data)
            img = Image.open(io.BytesIO(image_data))
            img = img.resize((1080, 1920))
            img.save(image_path)
            return image_path

    # Fallback - create branded placeholder image
    img = Image.new("RGB", (1080, 1920), (10, 22, 40))
    img.save(image_path)
    return image_path
