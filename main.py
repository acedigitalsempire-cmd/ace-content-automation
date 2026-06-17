import os
import sys
import datetime
import traceback
from content_generator import (
    generate_script, generate_image,
    get_todays_topic, get_angle_for_slot
)
from video_builder import build_video
from publisher import publish_instagram, publish_facebook, publish_youtube
from config import PHOTOS


def get_slot_number():
    hour = datetime.datetime.utcnow().hour
    slot_map = {5: 0, 8: 1, 11: 2, 14: 3, 17: 4, 20: 5}
    return slot_map.get(hour, 0)


def run():
    print("=" * 50)
    print("ACE CONTENT AUTOMATION STARTING")
    print(f"Time UTC: {datetime.datetime.utcnow()}")
    print("=" * 50)

    try:
        slot = get_slot_number()
        print(f"Slot: {slot}")

        topic = get_todays_topic()
        angle = get_angle_for_slot(slot)
        photo_path = PHOTOS[slot % len(PHOTOS)]

        print(f"Topic: {topic}")
        print(f"Angle: {angle}")
        print(f"Photo: {photo_path}")

        # Step 1 - Generate script
        print("\nSTEP 1: Generating script...")
        content = generate_script(topic, angle, slot)
        caption = content["caption"]
        youtube_title = content["youtube_title"]
        scenes = content["scenes"]
        print(f"Script ready. Scenes: {len(scenes)}")

        # Step 2 - Generate images
        print("\nSTEP 2: Generating images...")
        image_paths = []
        for i, scene in enumerate(scenes):
            path = generate_image(scene["image_prompt"], i)
            image_paths.append(path)

        # Step 3 - Build video
        print("\nSTEP 3: Building video...")
        video_path = build_video(scenes, image_paths, photo_path)
        print(f"Video ready: {video_path}")

        # Step 4 - Publish
        print("\nSTEP 4: Publishing...")
        ig_result = publish_instagram(video_path, caption)
        fb_result = publish_facebook(video_path, caption)
        yt_result = publish_youtube(video_path, youtube_title, caption)

        print("\n" + "=" * 50)
        print("AUTOMATION COMPLETE")
        print(f"Instagram: {'OK' if ig_result else 'FAILED'}")
        print(f"Facebook: {'OK' if fb_result else 'FAILED'}")
        print(f"YouTube: {'OK' if yt_result else 'FAILED'}")
        print("=" * 50)

    except Exception as e:
        print(f"\nAUTOMATION FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run()
