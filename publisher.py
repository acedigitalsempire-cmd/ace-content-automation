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


def upload_to_temp_host(video_path):
    print("Uploading video to temp host...")

    # Try file.io first
    try:
        with open(video_path, "rb") as f:
            response = requests.post(
                "https://file.io/?expires=1d",
                files={"file": ("video.mp4", f, "video/mp4")}
            )
        print(f"file.io status: {response.status_code}")
        print(f"file.io response: {response.text[:300]}")

        if response.status_code == 200:
            result = response.json()
            if result.get("success") and result.get("link"):
                url = result["link"]
                print(f"Temp URL: {url}")
                return url
    except Exception as e:
        print(f"file.io failed: {e}")

    # Try 0x0.st backup
    try:
        print("Trying 0x0.st backup...")
        with open(video_path, "rb") as f:
            response = requests.post(
                "https://0x0.st",
                files={"file": ("video.mp4", f, "video/mp4")}
            )
        print(f"0x0.st status: {response.status_code}")
        if response.status_code == 200:
            url = response.text.strip()
            print(f"Backup URL: {url}")
            return url
    except Exception as e:
        print(f"0x0.st failed: {e}")

    print("All upload attempts failed")
    return None


def publish_instagram(video_path, caption):
    print("Publishing to Instagram...")
    try:
        video_url = upload_to_temp_host(video_path)

        if not video_url:
            print("No video URL available for Instagram")
            return None

        # Step 1 - Create container
        response = requests.post(
            f"https://graph.facebook.com/v22.0/{INSTAGRAM_USER_ID}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "share_to_feed": "true",
                "access_token": META_ACCESS_TOKEN
            }
        )
        result = response.json()
        container_id = result.get("id")
        print(f"IG Container ID: {container_id}")

        if not container_id:
            print(f"IG container error: {result}")
            return None

        # Step 2 - Poll until FINISHED
        print("Polling IG container status...")
        for attempt in range(20):
            status_response = requests.get(
                f"https://graph.facebook.com/v22.0/{container_id}",
                params={
                    "fields": "status_code",
                    "access_token": META_ACCESS_TOKEN
                }
            )
            status = status_response.json()
            status_code = status.get("status_code")
            print(f"IG Status attempt {attempt + 1}: {status_code}")

            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                print(f"IG processing error: {status}")
                return None
            time.sleep(15)

        # Step 3 - Publish
        publish_response = requests.post(
            f"https://graph.facebook.com/v22.0/{INSTAGRAM_USER_ID}/media_publish",
            data={
                "creation_id": container_id,
                "access_token": META_ACCESS_TOKEN
            }
        )
        result = publish_response.json()
        print(f"Instagram published: {result}")
        return result

    except Exception as e:
        print(f"Instagram error: {e}")
        return None


def publish_facebook(video_path, caption):
    print("Publishing to Facebook...")
    try:
        video_url = upload_to_temp_host(video_path)

        if not video_url:
            print("No video URL available for Facebook")
            return None

        url = f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/video_reels"

        # Step 1 - Start upload
        start_response = requests.post(
            url,
            data={
                "upload_phase": "start",
                "access_token": META_ACCESS_TOKEN
            }
        )
        video_id = start_response.json().get("video_id")
        print(f"FB Video ID: {video_id}")

        if not video_id:
            print(f"FB start error: {start_response.json()}")
            return None

        # Step 2 - Finish upload
        finish_response = requests.post(
            url,
            data={
                "upload_phase": "finish",
                "video_id": video_id,
                "video_url": video_url,
                "description": caption,
                "video_state": "PUBLISHED",
                "access_token": META_ACCESS_TOKEN
            }
        )
        result = finish_response.json()
        print(f"Facebook published: {result}")
        return result

    except Exception as e:
        print(f"Facebook error: {e}")
        return None


def publish_youtube(video_path, title, caption):
    print("Publishing to YouTube...")
    try:
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
                "description": f"{caption}\n\n#AceDigitalsGlobal #DigitalUche #BusinessGrowth #NigerianBusiness #DigitalMarketing",
                "tags": [
                    "business growth", "digital marketing",
                    "AI automation", "Nigerian business",
                    "website", "DigitalUche", "AceDigitalsGlobal"
                ],
                "categoryId": "28"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
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
        video_id = response.get("id")
        print(f"YouTube published: https://youtube.com/shorts/{video_id}")
        return response

    except Exception as e:
        print(f"YouTube error: {e}")
        return None
