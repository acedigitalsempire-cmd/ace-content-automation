import google.generativeai as genai
import requests
import os
from config import GEMINI_API_KEY, BRAND_NAME, BRAND_NICHE, BRAND_AUDIENCE

genai.configure(api_key=GEMINI_API_KEY)

def generate_topic_and_script():
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    You are a content strategist for {BRAND_NAME}, a digital marketing agency.
    Target audience: {BRAND_AUDIENCE}
    Niche: {BRAND_NICHE}
    
    Generate a short educational video topic and script.
    
    Return ONLY this JSON format, nothing else:
    {{
        "topic": "video topic here",
        "caption": "engaging social media caption with relevant hashtags",
        "scenes": [
            {{
                "text": "text to show on screen (max 10 words)",
                "voiceover": "what the narrator says for this scene",
                "image_prompt": "detailed prompt to generate relevant image"
            }}
        ]
    }}
    
    Rules:
    - Maximum 6 scenes
    - Each voiceover max 30 words
    - Make it educational and valuable
    - Focus on AI tools, digital marketing, or tech for business
    - Caption must include 5 relevant hashtags
    """
    
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    # Clean JSON
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    import json
    return json.loads(text)


def generate_image(prompt, index):
    import google.generativeai as genai
    from PIL import Image
    import io
    
    model = genai.ImageGenerationModel("imagen-3.0-generate-002")
    
    full_prompt = f"{prompt}, professional, clean, modern, tech style, no text overlay"
    
    result = model.generate_images(
        prompt=full_prompt,
        number_of_images=1,
        aspect_ratio="9:16"
    )
    
    image_path = f"/tmp/scene_{index}.png"
    
    for image in result.images:
        img = Image.open(io.BytesIO(image._pil_image.tobytes()))
        img.save(image_path)
        break
    
    return image_path
