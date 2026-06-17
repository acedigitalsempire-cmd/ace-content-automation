from google import genai
from google.genai import types
import json
import base64
import io
from PIL import Image
from config import GEMINI_API_KEY, BRAND_NAME, BRAND_NICHE, BRAND_AUDIENCE

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_topic_and_script():
    prompt = f"""You are a content strategist for {BRAND_NAME}, a digital marketing agency.
Target audience: Nigerian entrepreneurs and SME owners aged 18-35.
Niche: {BRAND_NICHE}

Generate a short educational video topic and script.

Return ONLY valid JSON, no markdown, no backticks, no explanation:
{{
    "topic": "video topic here",
    "caption": "engaging caption with 5 hashtags",
    "scenes": [
        {{
            "text": "max 10 words on screen",
            "voiceover": "narrator speech max 30 words",
            "image_prompt": "detailed image generation prompt"
        }}
    ]
}}

Rules:
- Exactly 4 scenes
- Return pure JSON only
- Focus on AI tools, digital marketing, or tech for business"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = response.text.strip()
    print(f"Raw Gemini response: {text[:200]}")

    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)
    print(f"Parsed successfully. Scenes: {len(data['scenes'])}")
    return data


def generate_image(prompt, index):
    image_path = f"/tmp/scene_{index}.png"

    try:
        print(f"Calling Gemini image generation for scene {index}...")

        response = client.models.generate_content(
            model="gemini-3.1-flash-image",
            contents=f"{prompt}, professional, clean, modern, tech style, no text overlay"
        )

        for part in response.parts:
            if part.inline_data is not None:
                img = part.as_image()
                img = img.resize((1080, 1920))
                img.save(image_path)
                print(f"Image {index} generated successfully")
                return image_path

        print(f"No image in response for scene {index}, using fallback")

    except Exception as e:
        print(f"Image generation failed for scene {index}: {e}")

    # Fallback branded navy background
    img = Image.new("RGB", (1080, 1920), (10, 22, 40))
    img.save(image_path)
    print(f"Fallback image saved for scene {index}")
    return image_path
