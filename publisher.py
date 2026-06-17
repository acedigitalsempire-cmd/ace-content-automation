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


def upload_video_to_meta(video_path, ig_container_id):
    print("Uploading video directly to Meta servers...")
    file_size = os.path.getsize(video_path)

    headers = {
        "Authorization": f"OAuth {META_ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(file_size)
    }

    upload_url = f"https://rupload.facebook.com/ig-api-upload/v22.0/{ig_container_id}"

    with open(video_path, "rb") as f:
        response = requests.post(upload_url, headers=headers, data=f)

    print(f"Meta upload status: {response.status_code}")
    print(f"Meta upload response: {response.text[:300]}")
    return response.status_code in [200, 201]


def publish_instagram(video_path, caption):
    print("Publishing to Instagram...")
    try:
        file_size = os.path.getsize(video_path)
        print(f"Video size: {file_size} bytes")

        # Step 1 - Create resumable upload container
        container_response = requests.post(
            f"https://graph.facebook.com/v22.0/{INSTAGRAM_USER_ID}/media",
            data={
                "media_type": "REELS",
                "upload_type": "resumable",
                "caption": caption,
                "share_to_feed": "true",
                "access_token": META_ACCESS_TOKEN
            }
        )
        container_result = container_response.json()
        print(f"IG Container response: {container_result}")
        container_id = container_result.get("id")

        if not container_id:
            print(f"IG container creation failed: {container_result}")
            return None

        print(f"IG Container ID: {container_id}")

        # Step 2 - Upload video directly to Meta
        upload_success = upload_video_to_meta(video_path, container_id)

        if not upload_success:
            print("Video upload to Meta failed")
            return None

        # Step 3 - Poll until FINISHED
        print("Polling IG container status...")
        for attempt in range(30):
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
            time.sleep(10)

        # Step 4 - Publish
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
        import traceback
        traceback.print_exc()
        return None


def publish_facebook(video_path, caption):
    print("Publishing to Facebook...")
    try:
        file_size = os.path.getsize(video_path)

        # Step 1 - Start resumable upload
        start_response = requests.post(
            f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/video_reels",
            data={
                "upload_phase": "start",
                "access_token": META_ACCESS_TOKEN
            }
        )
        start_result = start_response.json()
        print(f"FB start response: {start_result}")
        video_id = start_result.get("video_id")
        upload_url = start_result.get("upload_url")

        if not video_id or not upload_url:
            print(f"FB start failed: {start_result}")
            return None

        print(f"FB Video ID: {video_id}")

        # Step 2 - Upload video to Facebook
        headers = {
            "Authorization": f"OAuth {META_ACCESS_TOKEN}",
            "offset": "0",
            "file_size": str(file_size)
        }

        with open(video_path, "rb") as f:
            upload_response = requests.post(upload_url, headers=headers, data=f)

        print(f"FB upload status: {upload_response.status_code}")
        print(f"FB upload response: {upload_response.text[:300]}")

        # Step 3 - Finish and publish
        finish_response = requests.post(
            f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/video_reels",
            data={
                "upload_phase": "finish",
                "video_id": video_id,
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
        import traceback
        traceback.print_exc()
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
                "tags": ["business growth", "digital marketing", "AI automation", "Nigerian business", "DigitalUche"],
                "categoryId": "28"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        video_id = response.get("id")
        print(f"YouTube published: https://youtube.com/shorts/{video_id}")
        return response

    except Exception as e:
        print(f"YouTube error: {e}")
        return None
