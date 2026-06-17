import schedule
import time
import threading
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
    print("Starting automation run...")

    try:
        # Step 1 - Generate topic and script
        print("Generating content...")
        content = generate_topic_and_script()
        topic = content["topic"]
        caption = content["caption"]
        scenes = content["scenes"]
        print(f"Topic: {topic}")

        # Step 2 - Generate images for each scene
        print("Generating images...")
        image_paths = []
        for i, scene in enumerate(scenes):
            image_path = generate_image(scene["image_prompt"], i)
            image_paths.append(image_path)
            print(f"Image {i+1} generated")

        # Step 3 - Build video
        print("Building video...")
        video_path = build_video(scenes, image_paths)
        print(f"Video built: {video_path}")

        # Step 4 - Publish to all platforms
        publish_instagram(video_path, caption)
        publish_facebook(video_path, caption)
        publish_youtube(video_path, topic, caption)

        print("Automation complete!")

    except Exception as e:
        print(f"Automation error: {e}")


def schedule_jobs():
    # Run once daily at 9AM
    schedule.every().day.at("09:00").do(run_automation)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(
        target=schedule_jobs,
        daemon=True
    )
    scheduler_thread.start()

    # Start Flask server
    app.run(host="0.0.0.0", port=10000)
