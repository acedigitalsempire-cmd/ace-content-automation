import os
import requests
import numpy as np
import scipy.io.wavfile as wav
import subprocess
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from config import (
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
    VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    NAVY, GOLD, WHITE, DARK, BRAND_NAME, BRAND_HANDLE
)

# Color themes for motion graphics
THEMES = {
    "navy_gold": {"bg": (10, 22, 40), "accent": (184, 146, 42), "text": (255, 255, 255)},
    "dark_green": {"bg": (8, 28, 20), "accent": (46, 184, 100), "text": (255, 255, 255)},
    "charcoal_white": {"bg": (30, 30, 35), "accent": (220, 220, 220), "text": (255, 255, 255)},
    "midnight_blue": {"bg": (5, 15, 45), "accent": (100, 150, 255), "text": (255, 255, 255)},
}


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
            "stability": 0.55,
            "similarity_boost": 0.75,
            "style": 0.15,
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
        print("Audio too small - error response")
        return None

    return audio_path


def create_silent_audio(duration, index):
    audio_path = f"/tmp/silent_{index}.wav"
    sample_rate = 44100
    samples = np.zeros(int(sample_rate * duration), dtype=np.int16)
    wav.write(audio_path, sample_rate, samples)
    return audio_path


def create_motion_graphic_frame(scene_text, voiceover_text, theme_name, frame_num, total_frames, scene_index, total_scenes):
    theme = THEMES.get(theme_name, THEMES["navy_gold"])
    bg_color = theme["bg"]
    accent_color = theme["accent"]
    text_color = theme["text"]

    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)

    # Animated progress — subtle brightness pulse based on frame
    progress = frame_num / max(total_frames, 1)

    # Top gradient bar
    bar_height = 8
    for x in range(VIDEO_WIDTH):
        bar_progress = x / VIDEO_WIDTH
        if bar_progress <= progress:
            draw.rectangle([x, 0, x + 1, bar_height], fill=accent_color)
        else:
            dark_accent = tuple(max(0, c // 4) for c in accent_color)
            draw.rectangle([x, 0, x + 1, bar_height], fill=dark_accent)

    # Load fonts
    try:
        font_huge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_huge = ImageFont.load_default()
        font_large = font_huge
        font_medium = font_huge
        font_small = font_huge
        font_tiny = font_huge

    # Decorative vertical accent line left
    draw.rectangle([0, 100, 6, VIDEO_HEIGHT - 100], fill=accent_color)

    # Brand name top
    brand_y = 40
    draw.text((30, brand_y), BRAND_NAME, font=font_small, fill=accent_color)
    handle_bbox = draw.textbbox((0, 0), BRAND_HANDLE, font=font_small)
    handle_w = handle_bbox[2] - handle_bbox[0]
    draw.text((VIDEO_WIDTH - handle_w - 30, brand_y), BRAND_HANDLE, font=font_small, fill=text_color)

    # Main scene text — large centered in upper middle area
    words = scene_text.upper().split()
    lines = []
    current_line = ""
    for word in words:
        test = current_line + word + " "
        bbox = draw.textbbox((0, 0), test, font=font_huge)
        if bbox[2] - bbox[0] < VIDEO_WIDTH - 120:
            current_line = test
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())

    # Center the text block vertically in upper 60%
    line_height = 85
    total_text_height = len(lines) * line_height
    start_y = (VIDEO_HEIGHT * 0.3) - (total_text_height / 2)
    start_y = max(150, start_y)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_huge)
        w = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - w) // 2

        # Shadow effect
        draw.text((x + 3, start_y + (i * line_height) + 3), line, font=font_huge, fill=(0, 0, 0))
        # Main text
        draw.text((x, start_y + (i * line_height)), line, font=font_huge, fill=accent_color)

    # Accent divider line
    divider_y = int(VIDEO_HEIGHT * 0.62)
    draw.rectangle([60, divider_y, VIDEO_WIDTH - 60, divider_y + 3], fill=accent_color)

    # Voiceover text subtitle at bottom
    vo_words = voiceover_text.split()
    vo_lines = []
    vo_current = ""
    for word in vo_words:
        test = vo_current + word + " "
        bbox = draw.textbbox((0, 0), test, font=font_medium)
        if bbox[2] - bbox[0] < VIDEO_WIDTH - 120:
            vo_current = test
        else:
            if vo_current:
                vo_lines.append(vo_current.strip())
            vo_current = word + " "
    if vo_current:
        vo_lines.append(vo_current.strip())

    vo_y = divider_y + 30
    for line in vo_lines[:4]:
        bbox = draw.textbbox((0, 0), line, font=font_medium)
        w = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - w) // 2
        draw.text((x, vo_y), line, font=font_medium, fill=text_color)
        vo_y += 48

    # Scene counter dots at bottom
    dot_y = VIDEO_HEIGHT - 80
    dot_spacing = 40
    total_dots_width = (total_scenes - 1) * dot_spacing
    dot_start_x = (VIDEO_WIDTH - total_dots_width) // 2

    for s in range(total_scenes):
        dot_x = dot_start_x + (s * dot_spacing)
        if s == scene_index:
            draw.ellipse([dot_x - 8, dot_y - 8, dot_x + 8, dot_y + 8], fill=accent_color)
        else:
            draw.ellipse([dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5], fill=tuple(c // 3 for c in accent_color))

    # Bottom brand strip
    strip_y = VIDEO_HEIGHT - 40
    draw.rectangle([0, strip_y, VIDEO_WIDTH, VIDEO_HEIGHT], fill=tuple(max(0, c - 5) for c in bg_color))
    footer_text = "acedigitalsempire.com"
    ft_bbox = draw.textbbox((0, 0), footer_text, font=font_tiny)
    ft_w = ft_bbox[2] - ft_bbox[0]
    draw.text(((VIDEO_WIDTH - ft_w) // 2, strip_y + 8), footer_text, font=font_tiny, fill=tuple(c // 2 for c in accent_color))

    return img


def build_scene_clip(scene, scene_index, total_scenes, audio_path, duration):
    theme = scene.get("color_theme", "navy_gold")
    fps = FPS
    total_frames = int(duration * fps)

    frames = []
    save_every = 3  # Save every 3rd frame for performance

    frame_paths = []
    for frame_num in range(0, total_frames, save_every):
        frame_img = create_motion_graphic_frame(
            scene["text"],
            scene["voiceover"],
            theme,
            frame_num,
            total_frames,
            scene_index,
            total_scenes
        )
        frame_path = f"/tmp/frame_{scene_index}_{frame_num}.png"
        frame_img.save(frame_path)
        frame_paths.append(frame_path)

    # Use first frame as base clip then write video with ffmpeg directly
    base_frame_path = f"/tmp/base_{scene_index}.png"
    frame_paths[0] if frame_paths else None

    # Create video from first frame (static with audio for simplicity)
    frame_img = create_motion_graphic_frame(
        scene["text"],
        scene["voiceover"],
        theme,
        0,
        total_frames,
        scene_index,
        total_scenes
    )
    frame_img.save(base_frame_path)

    scene_video_path = f"/tmp/scene_{scene_index}.mp4"

    # Use ffmpeg directly for better codec control
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", base_frame_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        scene_video_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}")
        return None

    print(f"Scene {scene_index} video created: {scene_video_path}")
    return scene_video_path


def build_video(scenes, photo_path=None):
    default_duration = 5
    scene_videos = []

    for i, scene in enumerate(scenes):
        print(f"Building scene {i + 1} of {len(scenes)}...")

        audio_path = generate_voiceover(scene["voiceover"], i)

        if audio_path and os.path.exists(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                audio_clip.close()
                print(f"Scene {i + 1} duration: {duration:.1f}s")
            except Exception as e:
                print(f"Audio duration error: {e}")
                duration = default_duration
                audio_path = None
        else:
            duration = default_duration
            audio_path = None

        if not audio_path:
            silent_path = create_silent_audio(default_duration, i)
            audio_path = silent_path
            duration = default_duration

        scene_video = build_scene_clip(scene, i, len(scenes), audio_path, duration)

        if scene_video:
            scene_videos.append(scene_video)
        else:
            print(f"Scene {i + 1} failed, skipping")

    if not scene_videos:
        raise Exception("No scene videos were created")

    # Concatenate all scene videos with ffmpeg
    output_path = "/tmp/final_video.mp4"

    if len(scene_videos) == 1:
        import shutil
        shutil.copy(scene_videos[0], output_path)
    else:
        # Create concat list
        concat_file = "/tmp/concat.txt"
        with open(concat_file, "w") as f:
            for sv in scene_videos:
                f.write(f"file '{sv}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-ar", "48000",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Concat error: {result.stderr}")
            raise Exception("Video concatenation failed")

    print(f"Final video: {output_path}")
    print(f"Size: {os.path.getsize(output_path)} bytes")
    return output_path
