from google import genai
import json
import datetime
import time
from config import (
    GEMINI_API_KEY, BRAND_NAME, BRAND_HANDLE,
    BRAND_NICHE, BRAND_AUDIENCE, TOPICS, ANGLES
)

client = genai.Client(api_key=GEMINI_API_KEY)

MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
]


def get_todays_topic():
    day = datetime.datetime.now().timetuple().tm_yday
    return TOPICS[day % len(TOPICS)]


def get_random_angle():
    hour = datetime.datetime.now().hour
    return ANGLES[hour % len(ANGLES)]


def generate_with_fallback(prompt):
    last_error = None
    for model in MODELS:
        try:
            print(f"Trying model: {model}")
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            print(f"Success with: {model}")
            return response.text
        except Exception as e:
            print(f"Model {model} failed: {e}")
            last_error = e
            time.sleep(3)
    raise Exception(f"All models failed: {last_error}")


def generate_script(topic=None, angle=None):
    if not topic:
        topic = get_todays_topic()
    if not angle:
        angle = get_random_angle()

    angle_instructions = {
        "direct_explanation": "Direct educational explanation. State the problem clearly. Explain why it happens. Give the solution. Tone: calm authoritative consultant.",
        "mistake_angle": "Common mistake businesses make. Start with the mistake. Show why it costs them. Give the correct approach. Tone: direct slightly urgent.",
        "case_study": "Real business scenario. Describe a business with the problem. Walk through what went wrong. Show the fix and result. Tone: storytelling relatable.",
        "myth_busting": "Challenge a common belief. State what most people believe. Bust it with real truth. Back it up with example. Tone: confident slightly provocative.",
        "fix_how_to": "Practical step by step fix. Identify the core problem. Give 3 clear actionable steps. Show what changes when fixed. Tone: practical helpful.",
        "pain_emotional": "Connect with business owner frustration. Start with their daily pain. Use ONE Nigerian expression naturally. Show they are not alone then give the insight. Tone: empathetic real conversational."
    }

    prompt = f"""You are the voice of {BRAND_NAME}, a business growth agency.
Founder: Uchenna Richard ({BRAND_HANDLE})
Target audience: {BRAND_AUDIENCE}
Niche: {BRAND_NICHE}

TOPIC: {topic}
ANGLE: {angle}
{angle_instructions[angle]}

BRAND VOICE RULES:
- Smart enough for a CEO, simple enough for an SME owner
- 80% professional English, max 20% Nigerian expressions for emphasis only
- Never say: leverage, delve, crucial, empower, game-changer, paradigm shift
- Never fake income claims or generic motivation without a business lesson
- Always diagnose a problem before prescribing a solution
- Short punchy sentences. No filler.
- Use contractions: you're, it's, don't, they've
- Speak directly: you, your business, your customers

ANTI AI RULES:
- No bullet point speaking
- No numbered lists in voiceover
- Natural pauses and rhythm
- Real specific examples
- Sounds like a person talking

SCENE RULES:
- Exactly 7 scenes
- Each scene is 7 seconds max when spoken aloud
- Each voiceover max 20 words (must be speakable in 7 seconds)
- Screen text is the KEY POINT in max 6 words
- Scenes must flow naturally as one continuous thought

MUSIC MOOD: Choose one that fits: educational, motivational, corporate, calm

Return ONLY this exact JSON, no markdown, no backticks:
{{
    "topic": "{topic}",
    "angle": "{angle}",
    "music_mood": "educational",
    "caption": "human sounding caption under 200 characters ending with a question, 5 hashtags",
    "youtube_title": "YouTube Shorts title under 60 characters",
    "scenes": [
        {{
            "scene_number": 1,
            "screen_text": "max 6 words shown on screen",
            "voiceover_guide": "exactly what to say, max 20 words, natural speech"
        }}
    ]
}}"""

    text = generate_with_fallback(prompt)

    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)
    print(f"Script ready. Topic: {data['topic']} | Angle: {data['angle']}")
    return data


def format_script_for_telegram(script_data):
    lines = []
    lines.append(f"🎬 *SCRIPT READY*")
    lines.append(f"📌 *Topic:* {script_data['topic']}")
    lines.append(f"🎯 *Angle:* {script_data['angle'].replace('_', ' ').title()}")
    lines.append(f"🎵 *Music Mood:* {script_data['music_mood'].title()}")
    lines.append("")
    lines.append("─" * 30)
    lines.append("")

    for scene in script_data["scenes"]:
        n = scene["scene_number"]
        lines.append(f"*Scene {n}* \\(~7 seconds\\)")
        lines.append(f"📺 *On Screen:* {scene['screen_text']}")
        lines.append(f"🎤 *You Say:* _{scene['voiceover_guide']}_")
        lines.append("")

    lines.append("─" * 30)
    lines.append("")
    lines.append(f"📝 *Caption:*")
    lines.append(script_data["caption"])
    lines.append("")
    lines.append(f"▶️ *YouTube Title:* {script_data['youtube_title']}")
    lines.append("")
    lines.append("✅ Record all 7 scenes then send them here one by one\\.")
    lines.append("Send /upload when you're ready to start uploading\\.")

    return "\n".join(lines)
