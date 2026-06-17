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
    return TOPICS[day_of_year % len(TOPICS)]


def get_angle_for_slot(slot_number):
    return ANGLES[slot_number % len(ANGLES)]


def generate_script(topic, angle, slot_number):
    angle_instructions = {
        "direct_explanation": "Write a direct educational explanation. State the problem in one sentence. Explain why it happens. Give the solution. Tone: calm authoritative consultant.",
        "mistake_angle": "Frame this as a common mistake businesses make. Start with the mistake. Show why it costs them money. Give the correct approach. Tone: direct slightly urgent.",
        "case_study": "Frame as a real business scenario. Describe a business with this problem. Walk through what went wrong. Show the fix and result. Tone: storytelling relatable specific.",
        "myth_busting": "Challenge a common belief. State what most people believe. Bust the myth with real truth. Back it up with a practical example. Tone: confident slightly provocative educational.",
        "fix_how_to": "Give a practical step by step fix. Identify the core problem. Give 3 clear actionable steps. End with what changes when fixed. Tone: practical helpful solution focused.",
        "pain_emotional": "Connect with the business owner frustration. Start with their daily pain. Use ONE Nigerian expression naturally. Show they are not alone then give the insight. Tone: empathetic real conversational. Use only one expression like: You fit get traffic and still no get sales. This one na silent business killer. Make we talk truth."
    }

    if slot_number in [0, 5]:
        length = "3 scenes, 20-35 seconds total"
    else:
        length = "5 scenes, 45-60 seconds total"

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
- Never use fake income claims or generic motivation without a business lesson
- Always diagnose a problem before prescribing a solution
- Short punchy sentences. No filler words.
- Use contractions: you're, it's, don't, they've
- Speak directly to viewer: you, your business, your customers
- Every sentence must earn its place

ANTI AI DETECTION:
- No bullet point style speaking
- No numbered lists in voiceover
- Natural pauses and rhythm
- Real specific examples not vague claims
- Sounds like a person talking not a document being read

Return ONLY this exact JSON, no markdown, no backticks:
{{
    "topic": "{topic}",
    "angle": "{angle}",
    "hook": "first 3-5 words that grab attention",
    "caption": "full social media caption that sounds human, ends with a question to drive comments, includes 5 relevant hashtags",
    "youtube_title": "YouTube Shorts title under 60 characters",
    "scenes": [
        {{
            "text": "max 8 words shown on screen",
            "voiceover": "what narrator says, natural speech, max 35 words",
            "color_theme": "one of: navy_gold, dark_green, charcoal_white, midnight_blue"
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
    print(f"Scenes: {len(data['scenes'])}")
    return data
