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
    try:
        file_size = os.path.getsize(video_path)
        print(f"Video size: {file_size} bytes")

        # Step 1 - Create resumable upload container
        response = requests.post(
            f"https://graph.facebook.com/v22.0/{INSTAGRAM_USER_ID}/media",
            params={
                "media_type": "REELS",
                "upload_type": "resumable",
                "caption": caption,
                "share_to_feed": "true",
                "access_token": META_ACCESS_TOKEN
            }
        )
        result = response.json()
        print(f"IG container response: {result}")

        container_id = result.get("id")
        upload_uri = result.get("uri")

        if not container_id:
            print(f"IG container failed: {result}")
            return None

        print(f"IG Container ID: {container_id}")

        # Step 2 - Upload binary directly to Meta
        upload_url = upload_uri or f"https://rupload.facebook.com/ig-api-upload/v22.0/{container_id}"

        with open(video_path, "rb") as f:
            upload_response = requests.post(
                upload_url,
                headers={
                    "Authorization": f"OAuth {META_ACCESS_TOKEN}",
                    "offset": "0",
                    "file_size": str(file_size)
                },
                data=f
            )

        print(f"IG upload status: {upload_response.status_code}")
        print(f"IG upload response: {upload_response.text[:300]}")

        if upload_response.status_code not in [200, 201]:
            print("IG binary upload failed")
            return None

        # Step 3 - Poll until FINISHED
        print("Polling IG status...")
        for attempt in range(30):
            status_resp = requests.get(
                f"https://graph.facebook.com/v22.0/{container_id}",
                params={
                    "fields": "status_code",
                    "access_token": META_ACCESS_TOKEN
                }
            )
            status = status_resp.json()
            code = status.get("status_code")
            print(f"IG attempt {attempt+1}: {code}")

            if code == "FINISHED":
                break
            elif code == "ERROR":
                print(f"IG error: {status}")
                return None
            time.sleep(10)

        # Step 4 - Publish
        publish_resp = requests.post(
            f"https://graph.facebook.com/v22.0/{INSTAGRAM_USER_ID}/media_publish",
            data={
                "creation_id": container_id,
                "access_token": META_ACCESS_TOKEN
            }
        )
        result = publish_resp.json()
        print(f"Instagram published: {result}")
        return result

    except Exception as e:
        import traceback
        print(f"Instagram error: {e}")
        traceback.print_exc()
        return None


def publish_facebook(video_path, caption):
    print("Publishing to Facebook...")
    try:
        file_size = os.path.getsize(video_path)

        # Step 1 - Initialize upload
        start_resp = requests.post(
            f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/video_reels",
            data={
                "upload_phase": "start",
                "access_token": META_ACCESS_TOKEN
            }
        )
        start_result = start_resp.json()
        print(f"FB start: {start_result}")

        video_id = start_result.get("video_id")
        upload_url = start_result.get("upload_url")

        if not video_id or not upload_url:
            print(f"FB init failed: {start_result}")
            return None

        print(f"FB Video ID: {video_id}")

        # Step 2 - Upload binary
        with open(video_path, "rb") as f:
            upload_resp = requests.post(
                upload_url,
                headers={
                    "Authorization": f"OAuth {META_ACCESS_TOKEN}",
                    "offset": "0",
                    "file_size": str(file_size)
                },
                data=f
            )

        print(f"FB upload status: {upload_resp.status_code}")
        print(f"FB upload response: {upload_resp.text[:300]}")

        # Step 3 - Finish and publish
        finish_resp = requests.post(
            f"https://graph.facebook.com/v22.0/{FACEBOOK_PAGE_ID}/video_reels",
            data={
                "upload_phase": "finish",
                "video_id": video_id,
                "description": caption,
                "video_state": "PUBLISHED",
                "access_token": META_ACCESS_TOKEN
            }
        )
        result = finish_resp.json()
        print(f"Facebook published: {result}")
        return result

    except Exception as e:
        import traceback
        print(f"Facebook error: {e}")
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
                "tags": ["business growth", "digital marketing", "AI", "Nigerian business", "DigitalUche"],
                "categoryId": "28"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        resp = req.execute()
        vid_id = resp.get("id")
        print(f"YouTube: https://youtube.com/shorts/{vid_id}")
        return resp

    except Exception as e:
        import traceback
        print(f"YouTube error: {e}")
        traceback.print_exc()
        return None
