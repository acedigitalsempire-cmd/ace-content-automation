import requests
import time
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import (
    META_ACCESS_TOKEN, INSTAGRAM_USER_ID,
    FACEBOOK_PAGE_ID, YOUTUBE_CLIENT_ID,
    YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN
)


def publish_instagram(video_path, caption):
    print("Publishing to Instagram...")

    # Step 1 - Upload video to a public URL first
    # We use a temp file hosting approach
    video_url = upload_to_temp_host(video_path)

    # Step 2 - Create container
    container_url = f"https://graph.facebook.com/v22.0/{INSTAGRAM_USER_ID}/media"
    container_data = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": META_ACCESS_TOKEN
    }
    response = requests.post(container_url, data=container_data)
    container_id = response.json().get("id")
    print(f"IG Container ID: {container_id}")

    # Step 3 - Poll until FINISHED
    status_url = f"https://graph.facebook.com/v22.0/{container_id}"
    for attempt in range(20):
        status = requests.get(status_url, params={
            "fields": "status_code",
            "access_token": META_ACCESS_TOKEN
        }).json()
        print(f"IG Status: {status}")
        if status.get("status_code") == "FINISHED":
            break
        time.sleep(15)

    # Step 4 - Publish
    publish_url = f"https://graph.facebook.com/v22.0/{INSTAGRAM_USER_ID}/media_publish"
    publish_data = {
        "creation_id": container_id,
        "access_token": META_ACCESS_TOKEN
    }
    result = requests.post(publish_url, data=publish_data)
    print(f"IG Published: {result.json()}")
    return result.json()


def publish_facebook(video_path, caption):
    print("Publishing to Facebook...")

    video_url = upload_to_temp_host(video_path)

    url = f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/video_reels"

    # Step 1 - Start upload
    start_data = {
        "upload_phase": "start",
        "access_token": META_ACCESS_TOKEN
    }
    response = requests.post(url, data=start_data)
    video_id = response.json().get("video_id")
    print(f"FB Video ID: {video_id}")

    # Step 2 - Finish upload
    finish_data = {
        "upload_phase": "finish",
        "video_id": video_id,
        "video_url": video_url,
        "description": caption,
        "video_state": "PUBLISHED",
        "access_token": META_ACCESS_TOKEN
    }
    result = requests.post(url, data=finish_data)
    print(f"FB Published: {result.json()}")
    return result.json()


def publish_youtube(video_path, title, caption):
    print("Publishing to YouTube...")

    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token"
    )

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": caption,
            "tags": ["AI", "digital marketing", "tech", "Nigeria", "business"],
            "categoryId": "28"
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = request.execute()
    print(f"YouTube Published: {response.get('id')}")
    return response


def upload_to_temp_host(video_path):
    # Upload to file.io for temporary public URL
    with open(video_path, "rb") as f:
        response = requests.post(
            "https://file.io",
            files={"file": f},
            data={"expires": "1d"}
        )
    url = response.json().get("link")
    print(f"Temp URL: {url}")
    return url
