import os
import requests
import talkingagents.settings as settings
import uuid
import time
import math
import pandas as pd


def download_video_from_url(video_url):
    try:
        base_dir = settings.BASE_DIR

        save_dir = os.path.join(base_dir, "tiktok_videos")
        os.makedirs(save_dir, exist_ok=True)

        response = requests.get(video_url, stream=True)
        if response.status_code != 200:
            raise Exception(
                f"Failed to download video, status code: {response.status_code}"
            )

        filename = video_url.split("/")[-1].split("?")[0] or "downloaded_video.mp4"
        save_path = os.path.join(save_dir, filename)

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return save_path
    except Exception as e:
        return None


def create_linkedin_content_post(access_token, urn, post_content):
    time.sleep(10)
    try:
        if not access_token or not urn or not post_content:
            return False
        post_url = f"{settings.LINKEDIN_API_URL}v2/ugcPosts"
        post_headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        post_body = {
            "author": urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post_content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        post_response = requests.post(post_url, headers=post_headers, json=post_body)

        if post_response.status_code in [200, 201]:
            return True
        return False
    except Exception as e:
        return False


def create_linkedin_image_post(access_token, urn, post_content, url):
    try:
        if not access_token or not urn or not url:
            return False

        image_file = requests.get(url)
        image_filename = f"{uuid.uuid4()}.jpg"
        save_dir = os.path.join(settings.BASE_DIR, "LinkedIn_images")
        os.makedirs(save_dir, exist_ok=True)
        image_path = os.path.join(save_dir, image_filename)

        with open(image_path, "wb+") as destination:
            for chunk in image_file.iter_content():
                destination.write(chunk)

        register_upload_url = (
            f"{settings.LINKEDIN_API_URL}v2/assets?action=registerUpload"
        )
        register_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        register_body = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        register_response = requests.post(
            register_upload_url, headers=register_headers, json=register_body
        )
        if register_response.status_code not in [200, 201]:
            return False

        register_data = register_response.json()
        upload_url = register_data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset = register_data["value"]["asset"]

        with open(image_path, "rb") as img_file:
            upload_headers = {
                "Authorization": f"Bearer {access_token}",
            }
            upload_response = requests.put(
                upload_url, headers=upload_headers, data=img_file
            )

        if upload_response.status_code not in [200, 201]:
            return False

        # Step 5: Create UGC Post with image
        post_url = f"{settings.LINKEDIN_API_URL}v2/ugcPosts"
        post_headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        post_body = {
            "author": urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post_content},
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {"text": "Image post"},
                            "media": asset,
                            "title": {"text": "LinkedIn Image Post"},
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        final_post_response = requests.post(
            post_url, headers=post_headers, json=post_body
        )
        if final_post_response.status_code in [200, 201]:
            return True
        return False
    except Exception as e:
        return False

    finally:
        if os.path.isfile(image_path):
            os.remove(image_path)


def upload_video_to_tiktok(access_token: str, video_url: str) -> bool:
    # time.sleep(60)
    if not access_token or not video_url:
        return False

    video_path = download_video_from_url(video_url=video_url)
    if not video_path:
        return False

    video_size = os.path.getsize(video_path)
    min_chunk = 5 * 1024 * 1024  # 5MB
    max_chunk = 64 * 1024 * 1024  # 64MB
    max_final_chunk = 128 * 1024 * 1024  # Final chunk up to 128MB
    max_chunks = 1000

    if video_size < min_chunk or video_size <= max_chunk:
        chunk_size = video_size
        total_chunk_count = 1
    else:
        chunk_size = min(max_chunk, math.ceil(video_size / max_chunks))
        total_chunk_count = math.floor(video_size / chunk_size)
        if video_size % chunk_size != 0:
            total_chunk_count += 1

    # Fetch creator info
    url = f"{settings.TIKTOK_API_URL}post/publish/creator_info/query/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    try:
        response = requests.post(url, headers=headers)
        if response.status_code not in [200, 201]:
            return False

        creator_data = response.json().get("data")
        if not creator_data:
            return False

        privacy_options = creator_data.get("privacy_level_options", ["SELF_ONLY"])
        comment_disabled = creator_data.get("comment_disabled", False)
        duet_disabled = creator_data.get("duet_disabled", False)
        stitch_disabled = creator_data.get("stitch_disabled", True)

        # Prepare video upload
        upload_video_url = f"{settings.TIKTOK_API_URL}post/publish/video/init/"
        post_video_headers = headers.copy()
        post_video_data = {
            "post_info": {
                "title": "this will be a funny #cat video on your @tiktok #fyp",
                "privacy_level": "SELF_ONLY",
                "disable_duet": duet_disabled,
                "disable_comment": comment_disabled,
                "disable_stitch": stitch_disabled,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count,
            },
        }

        post_video_response = requests.post(
            upload_video_url, headers=post_video_headers, json=post_video_data
        )
        if post_video_response.status_code not in [200, 201]:
            return False

        post_video_response_data = post_video_response.json().get("data")
        if not post_video_response_data:
            return False

        url_for_video_upload = post_video_response_data.get("upload_url")
        with open(video_path, "rb") as f:
            for i in range(total_chunk_count):
                start_byte = i * chunk_size
                end_byte = min((i + 1) * chunk_size - 1, video_size - 1)
                f.seek(start_byte)
                chunk_data = f.read(end_byte - start_byte + 1)
                upload_video_headers = {
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(chunk_data)),
                    "Content-Range": f"bytes {start_byte}-{end_byte}/{video_size}",
                }
                response_of_chunk_upload = requests.put(
                    url_for_video_upload,
                    headers=upload_video_headers,
                    data=chunk_data,
                    timeout=(10, 480),
                )
                if response_of_chunk_upload.status_code not in [200, 201]:
                    return False
    except Exception as e:
        print(f"Error while uploading video to TikTok: {e}")
        return False
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

    return True


def start_uploading_on_tiktok(posts_content_path, access_token):
    df = pd.read_csv(posts_content_path)
    for index, row in df.iterrows():
        video_url = row.get("video_url")
        if not video_url:
            print("Skipping Posting. No Video Url Found")
            continue
        upload_video_to_tiktok(access_token=access_token, video_url=video_url)


def start_posting_on_linkedin(access_token, posts_content_path, urn):
    try:
        df = pd.read_csv(posts_content_path)
        for index, row in df.iterrows():
            post_type = str(row["type"])
            content = str(row["content"])
            if post_type == "image":
                url = str(row["url"])
                if not url:
                    print("No URL found, Skipping Post: ", index)
                    continue
                if not content:
                    content = ""
                create_linkedin_image_post(
                    access_token=access_token, urn=urn, post_content=content, url=url
                )
            else:
                if not content:
                    print("No Content Found. Skipping Post ", index)
                    continue
                create_linkedin_content_post(
                    access_token=access_token, urn=urn, post_content=content
                )
    except Exception as e:
        return False
