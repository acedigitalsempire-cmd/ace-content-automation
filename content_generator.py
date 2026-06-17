from google import genai
from google.genai import types
import json
import datetime
from PIL import Image, ImageDraw
import io
import base64
from config import (
    GEMINI_API_KEY, BRAND_NAME, BRAND_HANDLE,
    BRAND_NICHE, BRAND_AUDIENCE, TOPICS, ANGLES,
    VIDEO_WIDTH, VIDEO_HEIGHT, NAVY, GOLD
)

client = genai.Client(api_key=GEMINI_API_KEY)


def get_todays_topic():
    day_of_year = datetime.datetime.now().timetuple().tm_yday
    topic_index = day_of_year % len(TOPICS)
    return TOPICS[topic_index]


def get_angle_for_slot(slot_number):
    return ANGLES[slot_number % len(ANGLES)]


def generate_script(topic, angle, slot_number):
    angle_instructions = {
        "direct_explanation": """
Write a direct educational explanation.
Start by stating the problem clearly in one sentence.
Then explain why it happens.
Then give the solution.
Tone: calm, authoritative consultant.""",

        "mistake_angle": """
Frame this as a common mistake businesses make.
Start with the mistake most people make.
Show why it is costing them money or customers.
Give the correct approach.
Tone: direct, slightly urgent but not alarmist.""",

        "case_study": """
Frame this as a real business scenario.
Start by describing a business facing this problem.
Walk through what went wrong.
Show what the fix was and the result.
Tone: storytelling, relatable, specific.""",

        "myth_busting": """
Challenge a common belief about this topic.
Start by stating what most people believe.
Then bust the myth with the real truth.
Back it up with a practical example.
Tone: confident, slightly provocative, educational.""",

        "fix_how_to": """
Give a practical step by step fix.
Start by identifying the core problem.
Give 3 clear actionable steps to fix it.
End with what changes when they fix it.
Tone: practical, helpful, solution focused.""",

        "pain_emotional": """
Connect emotionally with the business owner frustration.
Start with the pain they feel daily because of this problem.
Use ONE Nigerian expression naturally for relatability.
Examples: You fit get traffic and still no get sales.
This one na silent business killer.
Make we talk truth.
Show them they are not alone then give them the insight.
Tone: empathetic, real, slightly conversational."""
    }

    if slot_number in [0, 5]:
        length = "3 scenes, 20-35 seconds total, sharp hook quick insight strong punch line"
    else:
        length = "5 scenes, 45-60 seconds total, hook problem breakdown solution closing punch"

    prompt = f"""You are the voice of {BRAND_NAME}, a business growth and digital transformation agency.
Founder: Uchenna Richard ({BRAND_HANDLE})
Target audience: {BRAND_AUDIENCE}
Niche: {BRAND_NICHE}

TODAY TOPIC: {topic}
VIDEO ANGLE: {angle}
TARGET LENGTH: {length}

ANGLE INSTRUCTIONS:
{angle_instructions[angle]}

BRAND VOICE RULES:
- Smart enough for a CEO, simple enough for an SME owner
- 80% professional English, max 20% Nigerian expressions for emphasis only
- Never say: leverage, delve, crucial, empower, game-changer, paradigm shift, utilize
- Never use fake income claims or generic motivation
- Always diagnose a problem before prescribing a solution
- Short punchy sentences. No filler words.
- Use contractions naturally: you're, it's, don't, they've
- Speak directly to the viewer: you, your business, your customers
- Every sentence must earn its place

ANTI AI DETECTION RULES:
- No bullet point style speaking
- No numbered lists in the voiceover
- Natural pauses and rhythm
- Real specific examples not vague claims
- Sounds like a person talking not a document being read

Return ONLY this exact JSON, no markdown, no backticks, no explanation outside the JSON:
{{
    "topic": "{topic}",
    "angle": "{angle}",
    "hook": "first 3-5 words that grab attention",
    "caption": "full social media caption that sounds human, ends with a question to drive comments, includes 5 relevant hashtags",
    "youtube_title": "YouTube Shorts title under 60 characters",
    "scenes": [
        {{
            "text": "max 8 words shown on screen",
            "voiceover": "what the narrator says, natural speech, max 35 words per scene",
            "image_prompt": "detailed visual description for background image, no text, no people, professional business or tech environment"
        }}
    ]
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = response.text.strip()
    print(f"Raw response preview: {text[:300]}")

    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)
    print(f"Script generated. Topic: {data['topic']}")
    print(f"Angle: {data['angle']}")
    print(f"Hook: {data['hook']}")
    print(f"Scenes: {len(data['scenes'])}")
    return data


def generate_image(prompt, index):
    image_path = f"/tmp/scene_{index}.png"

    try:
        print(f"Generating image for scene {index}...")
        response = client.models.generate_content(
            model="imagen-3.0-generate-002",
            contents=f"{prompt}, professional, cinematic, dark moody lighting, navy and gold color palette, no text, no people",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                image_data = base64.b64decode(part.inline_data.data)
                img = Image.open(io.BytesIO(image_data))
                img = img.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
                img.save(image_path)
                print(f"Image {index} generated successfully")
                return image_path

        print(f"No image returned for scene {index}, using fallback")

    except Exception as e:
        print(f"Image generation error scene {index}: {e}")

    # Branded navy fallback
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), NAVY)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, VIDEO_HEIGHT - 4, VIDEO_WIDTH, VIDEO_HEIGHT], fill=GOLD)
    img.save(image_path)
    print(f"Fallback image saved for scene {index}")
    return image_path
