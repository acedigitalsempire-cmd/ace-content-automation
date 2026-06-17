import os
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from config import (
    ELEVENLABS_API_KEY,
    VIDEO_WIDTH, VIDEO_HEIGHT, FPS
)

NAVY = (10, 22, 40)
GOLD = (184, 146, 42)


def generate_voiceover(text, index):
    print(f"Generating voiceover for scene {index}...")
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
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

    print(f"ElevenLabs status: {response.status_code}")
    print(f"ElevenLabs content-type: {response.headers.get('content-type')}")

    if response.status_code != 200:
        print(f"ElevenLabs error: {response.text}")
        return None

    audio_path = f"/tmp/audio_{index}.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    file_size = os.path.getsize(audio_path)
    print(f"Audio saved: {audio_path} ({file_size} bytes)")

    if file_size < 1000:
        print(f"Audio file too small — likely an error response")
        return None

    return audio_path


def add_text_overlay(image_path, text, output_path):
    img = Image.open(image_path).resize((VIDEO_WIDTH, VIDEO_HEIGHT))

    overlay = Image.new("RGBA", (VIDEO_WIDTH, 300), (10, 22, 40, 200))
    img = img.convert("RGBA")
    img.paste(overlay, (0, VIDEO_HEIGHT - 300), overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
        )
        small_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32
        )
    except:
        font = ImageFont.load_default()
        small_font = font

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

    draw.text((20, 30), "Ace Digitals Global", font=small_font, fill=GOLD)
    img.save(output_path)
    return output_path


def create_silent_audio(duration, index):
    """Create a silent audio file as fallback"""
    import wave
    import struct
    import math

    audio_path = f"/tmp/audio_{index}.wav"
    sample_rate = 44100
    num_samples = int(sample_rate * duration)

    with wave.open(audio_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack('<h', 0))

    return audio_path


def build_video(scenes, image_paths):
    clips = []
    default_duration = 5

    for i, (scene, image_path) in enumerate(zip(scenes, image_paths)):
        print(f"Processing scene {i+1}...")

        overlay_path = f"/tmp/overlay_{i}.png"
        add_text_overlay(image_path, scene["text"], overlay_path)

        audio_path = generate_voiceover(scene["voiceover"], i)

        if audio_path and os.path.exists(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                print(f"Scene {i+1} duration: {duration}s")
                img_clip = ImageClip(overlay_path, duration=duration)
                img_clip = img_clip.with_audio(audio_clip)
            except Exception as e:
                print(f"Audio error scene {i+1}: {e}, using silent fallback")
                silent_path = create_silent_audio(default_duration, i)
                audio_clip = AudioFileClip(silent_path)
                img_clip = ImageClip(overlay_path, duration=default_duration)
                img_clip = img_clip.with_audio(audio_clip)
        else:
            print(f"No audio for scene {i+1}, using silent fallback")
            silent_path = create_silent_audio(default_duration, i)
            audio_clip = AudioFileClip(silent_path)
            img_clip = ImageClip(overlay_path, duration=default_duration)
            img_clip = img_clip.with_audio(audio_clip)

        clips.append(img_clip)
        print(f"Scene {i+1} clip ready")

    print("Concatenating all clips...")
    final = concatenate_videoclips(clips, method="compose")

    output_path = "/tmp/final_video.mp4"
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )
    print(f"Video written to {output_path}")
    return output_path
