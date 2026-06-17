import os
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from config import (
    ELEVENLABS_API_KEY, BRAND_COLORS,
    VIDEO_WIDTH, VIDEO_HEIGHT, FPS
)

NAVY = (10, 22, 40)
GOLD = (184, 146, 42)


def generate_voiceover(text, index):
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    audio_path = f"/tmp/audio_{index}.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)
    return audio_path


def add_text_overlay(image_path, text, output_path):
    img = Image.open(image_path).resize(
        (VIDEO_WIDTH, VIDEO_HEIGHT)
    )
    draw = ImageDraw.Draw(img)

    overlay = Image.new("RGBA", (VIDEO_WIDTH, 300), (10, 22, 40, 200))
    img = img.convert("RGBA")
    img.paste(overlay, (0, VIDEO_HEIGHT - 300), overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
        )
    except:
        font = ImageFont.load_default()

    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current + word) < 25:
            current += word + " "
        else:
            lines.append(current.strip())
            current = word + " "
    lines.append(current.strip())

    y = VIDEO_HEIGHT - 280
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - w) // 2
        draw.text((x, y), line, font=font, fill=GOLD)
        y += 60

    draw.text((20, 30), "Ace Digitals Global", font=font, fill=GOLD)

    img.save(output_path)
    return output_path


def build_video(scenes, image_paths):
    clips = []

    for i, (scene, image_path) in enumerate(zip(scenes, image_paths)):
        audio_path = generate_voiceover(scene["voiceover"], i)

        overlay_path = f"/tmp/overlay_{i}.png"
        add_text_overlay(image_path, scene["text"], overlay_path)

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        img_clip = ImageClip(overlay_path, duration=duration)
        img_clip = img_clip.with_audio(audio_clip)

        clips.append(img_clip)

    final = concatenate_videoclips(clips, method="compose")

    output_path = "/tmp/final_video.mp4"
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )

    return output_path
