import schedule
import time
import threading
import traceback
from flask import Flask
from content_generator import generate_topic_and_script, generate_image
from video_builder import build_video
from publisher import publish_instagram, publish_facebook, publish_youtube

app = Flask(__name__)

@app.route("/healthz")
def health():
    return "OK", 200

@app.route("/")
def home():
    return "ACE Content Automation Running", 200


def run_automation():
    print("=== AUTOMATION START ===")

    try:
        print("STEP 1: Generating topic and script...")
        content = generate_topic_and_script()
        topic = content["topic"]
        caption = content["caption"]
        scenes = content["scenes"]
        print(f"STEP 1 DONE: Topic = {topic}")

        print("STEP 2: Generating images...")
        image_paths = []
        for i, scene in enumerate(scenes):
            print(f"Generating image {i+1} of {len(scenes)}...")
            image_path = generate_image(scene["image_prompt"], i)
            image_paths.append(image_path)
            print(f"Image {i+1} saved to {image_path}")

        print("STEP 3: Building video...")
        video_path = build_video(scenes, image_paths)
        print(f"STEP 3 DONE: Video at {video_path}")

        print("STEP 4: Publishing to Instagram...")
        publish_instagram(video_path, caption)
        print("Instagram done.")

        print("STEP 5: Publishing to Facebook...")
        publish_facebook(video_path, caption)
        print("Facebook done.")

        print("STEP 6: Publishing to YouTube...")
        publish_youtube(video_path, topic, caption)
        print("YouTube done.")

        print("=== AUTOMATION COMPLETE ===")

    except Exception as e:
        print(f"=== AUTOMATION FAILED ===")
        print(f"Error: {e}")
        traceback.print_exc()


def schedule_jobs():
    schedule.every().day.at("09:00").do(run_automation)
    print("Running immediate test on startup...")
    run_automation()
    print("Startup test finished. Waiting for scheduled runs.")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    scheduler_thread = threading.Thread(
        target=schedule_jobs,
        daemon=True
    )
    scheduler_thread.start()

    app.run(host="0.0.0.0", port=10000)
