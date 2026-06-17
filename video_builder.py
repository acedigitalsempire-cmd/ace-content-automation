import os
import requests
import numpy as np
import scipy.io.wavfile as wav
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from config import (
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
    VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    NAVY, GOLD, WHITE
)


def generate_voiceover(text, index):
    print(f"Generating voiceover scene {index}...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.6,
            "similarity_boost": 0.8,
            "style": 0.2,
            "use_speaker_boost": True
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"ElevenLabs status: {response.status_code}")

    if response.status_code != 200:
        print(f"ElevenLabs error: {response.text[:300]}")
        return None

    audio_path = f"/tmp/audio_{index}.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    size = os.path.getsize(audio_path)
    print(f"Audio saved: {size} bytes")

    if size < 1000:
        print(f"Audio too small likely error response")
        return None

    return audio_path


def create_silent_audio(duration, index):
    audio_path = f"/tmp/silent_{index}.wav"
    sample_rate = 44100
    samples = np.zeros(int(sample_rate * duration), dtype=np.int16)
    wav.write(audio_path, sample_rate, samples)
    return audio_path


def add_branded_overlay(bg_image_path, photo_path, scene_text, output_path):
    bg = Image.open(bg_image_path).resize((VIDEO_WIDTH, VIDEO_HEIGHT))

    # Dark overlay on background
    overlay = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 120))
    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, overlay)
    bg = bg.convert("RGB")

    # Photo in upper 65%
    photo_height = int(VIDEO_HEIGHT * 0.65)
    try:
        photo = Image.open(photo_path)
        photo = photo.resize((VIDEO_WIDTH, photo_height))
        bg_upper = bg.crop((0, 0, VIDEO_WIDTH, photo_height))
        blended = Image.blend(
            bg_upper.convert("RGBA"),
            photo.convert("RGBA"),
            alpha=0.85
        )
        bg.paste(blended.convert("RGB"), (0, 0))
    except Exception as e:
        print(f"Photo overlay error: {e}")

    # Navy card bottom 35%
    card_top = int(VIDEO_HEIGHT * 0.65)
    card = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT - card_top), NAVY)
    bg.paste(card, (0, card_top))

    draw = ImageDraw.Draw(bg)

    # Gold accent line
    draw.rectangle(
        [0, card_top, VIDEO_WIDTH, card_top + 4],
        fill=GOLD
    )

    # Load fonts
    try:
        font_large = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52
        )
        font_brand = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
        )
    except:
        font_large = ImageFont.load_default()
        font_brand = font_large

    # Scene text in card
    words = scene_text.split()
    lines = []
    current = ""
    for word in words:
        test = current + word + " "
        bbox = draw.textbbox((0, 0), test, font=font_large)
        if bbox[2] - bbox[0] < VIDEO_WIDTH - 80:
            current = test
        else:
            if current:
                lines.append(current.strip())
            current = word + " "
    if current:
        lines.append(current.strip())

    text_y = card_top + 30
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_large)
        w = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - w) // 2
        draw.text((x, text_y), line, font=font_large, fill=GOLD)
        text_y += 65

    # Brand name top left
    draw.text((20, 20), "Ace Digitals Global", font=font_brand, fill=GOLD)

    # Handle top right
    handle = "@DigitalUche"
    bbox = draw.textbbox((0, 0), handle, font=font_brand)
    w = bbox[2] - bbox[0]
    draw.text((VIDEO_WIDTH - w - 20, 20), handle, font=font_brand, fill=WHITE)

    bg.save(output_path)
    return output_path


def build_video(scenes, image_paths, photo_path):
    clips = []
    default_duration = 5

    for i, (scene, image_path) in enumerate(zip(scenes, image_paths)):
        print(f"Building scene {i + 1} of {len(scenes)}...")

        overlay_path = f"/tmp/overlay_{i}.png"
        add_branded_overlay(image_path, photo_path, scene["text"], overlay_path)

        audio_path = generate_voiceover(scene["voiceover"], i)

        try:
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                print(f"Scene {i + 1} duration: {duration:.1f}s")
            else:
                raise Exception("No audio file")
        except Exception as e:
            print(f"Audio fallback scene {i + 1}: {e}")
            silent_path = create_silent_audio(default_duration, i)
            audio_clip = AudioFileClip(silent_path)
            duration = default_duration

        img_clip = ImageClip(overlay_path, duration=duration)
        img_clip = img_clip.with_audio(audio_clip)
        clips.append(img_clip)
        print(f"Scene {i + 1} ready")

    print("Concatenating all scenes...")
    final = concatenate_videoclips(clips, method="compose")

    output_path = "/tmp/final_video.mp4"
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )
    print(f"Video complete: {output_path}")
    print(f"Video size: {os.path.getsize(output_path)} bytes")
    return output_path
