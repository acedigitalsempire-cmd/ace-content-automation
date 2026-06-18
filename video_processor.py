import os
import subprocess
import requests
import tempfile
from config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS, MUSIC_MOODS


def download_music(mood):
    url = MUSIC_MOODS.get(mood, MUSIC_MOODS["educational"])
    music_path = f"/tmp/background_music.mp3"
    print(f"Downloading music for mood: {mood}")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(music_path, "wb") as f:
                f.write(response.content)
            print(f"Music downloaded: {os.path.getsize(music_path)} bytes")
            return music_path
    except Exception as e:
        print(f"Music download failed: {e}")
    return None


def add_captions_to_scene(video_path, screen_text, scene_index, output_path):
    print(f"Adding captions to scene {scene_index}...")

    # Get video duration
    probe_cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        video_path
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)

    # Build caption filter — CapCut style
    # Bold white text with black stroke, centered, lower third position
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    # Escape special characters for ffmpeg
    safe_text = screen_text.replace("'", "\\'").replace(":", "\\:").replace(",", "\\,")

    caption_filter = (
        f"drawtext="
        f"fontfile={font_path}:"
        f"text='{safe_text}':"
        f"fontcolor=white:"
        f"fontsize=72:"
        f"x=(w-text_w)/2:"
        f"y=h*0.78:"
        f"borderw=4:"
        f"bordercolor=black:"
        f"box=0:"
        f"shadowx=3:"
        f"shadowy=3:"
        f"shadowcolor=black@0.8"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", caption_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Caption error: {result.stderr[:300]}")
        # Return original if caption fails
        import shutil
        shutil.copy(video_path, output_path)

    return output_path


def merge_and_process(video_paths, script_data):
    print(f"Processing {len(video_paths)} video clips...")
    scenes = script_data["scenes"]
    music_mood = script_data.get("music_mood", "educational")

    # Step 1 — Add captions to each scene
    captioned_paths = []
    for i, (video_path, scene) in enumerate(zip(video_paths, scenes)):
        captioned_path = f"/tmp/captioned_{i}.mp4"
        add_captions_to_scene(
            video_path,
            scene["screen_text"],
            i,
            captioned_path
        )
        captioned_paths.append(captioned_path)
        print(f"Scene {i+1} captioned")

    # Step 2 — Merge all scenes
    print("Merging all scenes...")
    concat_file = "/tmp/concat_list.txt"
    with open(concat_file, "w") as f:
        for path in captioned_paths:
            f.write(f"file '{path}'\n")

    merged_path = "/tmp/merged_video.mp4"
    merge_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", "192k",
        "-movflags", "+faststart",
        merged_path
    ]

    result = subprocess.run(merge_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Merge failed: {result.stderr[:500]}")

    print(f"Merged video: {os.path.getsize(merged_path)} bytes")

    # Step 3 — Add background music
    music_path = download_music(music_mood)
    if not music_path:
        print("No music available, using merged video as final")
        return merged_path

    final_path = "/tmp/final_video.mp4"
    print("Adding background music...")

    music_cmd = [
        "ffmpeg", "-y",
        "-i", merged_path,
        "-i", music_path,
        "-filter_complex",
        "[0:a]volume=1.0[a1];[1:a]volume=0.08[a2];[a1][a2]amix=inputs=2:duration=first[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", "192k",
        "-movflags", "+faststart",
        final_path
    ]

    result = subprocess.run(music_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Music mix failed: {result.stderr[:300]}, using merged without music")
        return merged_path

    print(f"Final video with music: {os.path.getsize(final_path)} bytes")
    return final_path
