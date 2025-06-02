from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from .utils import (
    download_video_from_url,
    create_linkedin_content_post,
    create_linkedin_image_post,
    start_uploading_on_tiktok,
    start_posting_on_linkedin,
)
import requests
import talkingagents.settings as settings
import os
import math
import uuid
import pandas as pd
from threading import Thread
import hmac
import base64
import hashlib
from urllib.parse import quote, parse_qsl
import time


# Create your views here.


class CreateCSVFromExcell(APIView):
    def post(self, request):
        excell_file = request.data.get("excell_file", None)
        social_media_name = request.data.get("socialmedia_name", None)
        if (
            not excell_file
            or not excell_file.name.lower().endswith("xlsx")
            or not social_media_name
        ):
            return Response(
                {
                    "message": "No Excell File provided",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                }
            )
        csv_filename = "tiktok.csv"
        if social_media_name == "linkedin":
            csv_filename = "linkedin.csv"
        csv_path = os.path.join(settings.BASE_DIR, csv_filename)
        try:
            df = pd.read_excel(excell_file)
            if social_media_name == "linekdin":
                mandatory_cols = ["type", "content", "url"]
                if not all(col in df.columns for col in mandatory_cols):
                    return Response(
                        {
                            "message": f"Please Provide the as mandatory {mandatory_cols}",
                            "status": False,
                            "status_code": 400,
                            "response": None,
                        }
                    )
                df = df[mandatory_cols]
                df.to_csv(csv_path, index=False)
            else:
                mandatory_cols = ["video_url"]
                if not all(col in df.columns for col in mandatory_cols):
                    return Response(
                        {
                            "message": f"Please Provide the as mandatory {mandatory_cols}",
                            "status": False,
                            "status_code": 400,
                            "response": None,
                        }
                    )
                df = df[mandatory_cols]
                df.to_csv(csv_path, index=False)
        except Exception as e:
            print(f"Error converting Excel to CSV: {e}")
            return None
        return Response(
            {
                "message": "Csv Created Succesfilly",
                "status": True,
                "status_code": 200,
                "response": None,
            }
        )


class TwitterRequestTokenView(APIView):
    def post(self, request):
        url = "https://api.x.com/oauth/request_token"
        callback = "https://73a2-129-208-125-202.ngrok-free.app/x_success"
        consumer_key = settings.X_CONSUMER_ID
        consumer_secret = settings.X_CONSUMER_SECRET

        oauth_data = {
            "oauth_callback": callback,
            "oauth_consumer_key": consumer_key,
            "oauth_nonce": uuid.uuid4().hex,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_version": "1.0",
        }

        # Generate signature
        param_string = "&".join(
            f"{quote(k)}={quote(v)}" for k, v in sorted(oauth_data.items())
        )
        base_string = "&".join(
            [
                "POST",
                quote(url, safe=""),
                quote(param_string, safe=""),
            ]
        )
        signing_key = f"{quote(consumer_secret)}&"
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        oauth_data["oauth_signature"] = signature

        # Build Authorization header
        auth_header = "OAuth " + ", ".join(
            f'{k}="{quote(v)}"' for k, v in oauth_data.items()
        )
        headers = {
            "Authorization": auth_header,
            "User-Agent": "MyApp",
        }

        try:
            res = requests.post(url, headers=headers)
            res.raise_for_status()
            data = dict(parse_qsl(res.text))
            return Response(
                {
                    "message": "OAuth token received",
                    "status": True,
                    "token_data": data,
                }
            )
        except Exception as e:
            return Response(
                {
                    "message": "Failed to get request token",
                    "error": str(e),
                    "status": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyLinkedInView(APIView):
    def post(self, request):
        code = request.data.get("code", None)
        state = request.data.get("state", None)
        if not code:
            return Response(
                {
                    "message": "Please Provide me a code",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        url = f"{settings.LINKEDIN_BASE_URL}oauth/v2/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URL,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        get_access_token = requests.post(url, data=data, headers=headers)
        try:
            get_access_token.raise_for_status()
        except Exception as e:
            return Response(
                {
                    "message": "There was an error in request",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        response_tokens = get_access_token.json()
        print(response_tokens.get("access_token"))
        access_token = response_tokens.get("access_token")
        if not access_token:
            return Response(
                {
                    "message": "No Access Token Found",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        user_info_response = requests.get(
            f"{settings.LINKEDIN_API_URL}v2/userinfo", headers=headers
        )

        if user_info_response.status_code != 200:
            print(user_info_response)
            return Response(
                {
                    "message": "Failed to fetch user info from LinkedIn",
                    "status": False,
                    "status_code": user_info_response.status_code,
                    "response": None,
                },
                status=user_info_response.status_code,
            )
        user_info = user_info_response.json()
        urn = f"urn:li:person:{user_info.get('sub')}"
        if not urn:
            return Response(
                {
                    "message": "Person Profile info not found",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        posts_content_path = os.path.join(settings.BASE_DIR, "linkedin.csv")
        Thread(
            target=start_posting_on_linkedin,
            args=(access_token, posts_content_path, urn),
        ).start()
        return Response(
            {
                "message": "Successfully started posted on linkedin",
                "status": True,
                "status_code": 200,
                "response": None,
            },
            status=status.HTTP_200_OK,
        )


class CreatePostLinkedIn(APIView):
    def post(self, request):
        access_token = request.data.get("access_token")
        post_content = request.data.get("content")

        if not access_token or not post_content:
            return Response(
                {
                    "message": "Access Token and Content are required",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Step 1: Get user info from LinkedIn
        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        user_info_response = requests.get(
            f"{settings.LINKEDIN_API_URL}v2/userinfo", headers=headers
        )

        if user_info_response.status_code != 200:
            print(user_info_response)
            return Response(
                {
                    "message": "Failed to fetch user info from LinkedIn",
                    "status": False,
                    "status_code": user_info_response.status_code,
                    "response": None,
                },
                status=user_info_response.status_code,
            )

        user_info = user_info_response.json()
        urn = f"urn:li:person:{user_info.get('sub')}"

        # Step 2: Create LinkedIn post for text
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
            return Response(
                {
                    "message": "Post created successfully on LinkedIn",
                    "status": True,
                    "status_code": 200,
                    "response": post_response.json(),
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "message": "Failed to create LinkedIn post",
                "status": False,
                "status_code": post_response.status_code,
                "response": post_response.json(),
            },
            status=post_response.status_code,
        )


class UploadImageToLinkedInView(APIView):
    def post(self, request):
        access_token = request.data.get("access_token")
        post_content = request.data.get("content")
        image_file = request.FILES.get("image")

        if not access_token or not post_content or not image_file:
            return Response(
                {
                    "message": "Access Token, Content, and Image are required",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Step 1: Save image locally
        image_filename = f"{uuid.uuid4()}.jpg"
        save_dir = os.path.join(settings.BASE_DIR, "LinkedIn_images")
        os.makedirs(save_dir, exist_ok=True)
        image_path = os.path.join(save_dir, image_filename)

        with open(image_path, "wb+") as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        # Step 2: Get LinkedIn user info
        user_info_url = f"{settings.LINKEDIN_API_URL}v2/userinfo"
        user_headers = {
            "Authorization": f"Bearer {access_token}",
        }
        user_info_response = requests.get(user_info_url, headers=user_headers)
        if user_info_response.status_code != 200:
            return Response(
                {
                    "message": "Failed to fetch user info from LinkedIn",
                    "status": False,
                    "status_code": user_info_response.status_code,
                    "response": user_info_response.json(),
                },
                status=user_info_response.status_code,
            )
        user_info = user_info_response.json()
        urn = f"urn:li:person:{user_info.get('sub')}"

        # Step 3: Register image upload
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
            return Response(
                {
                    "message": "Failed to register image upload",
                    "status": False,
                    "status_code": register_response.status_code,
                    "response": register_response.json(),
                },
                status=register_response.status_code,
            )

        register_data = register_response.json()
        upload_url = register_data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset = register_data["value"]["asset"]

        # Step 4: Upload image to LinkedIn
        with open(image_path, "rb") as img_file:
            upload_headers = {
                "Authorization": f"Bearer {access_token}",
            }
            upload_response = requests.put(
                upload_url, headers=upload_headers, data=img_file
            )

        if upload_response.status_code not in [200, 201]:
            return Response(
                {
                    "message": "Failed to upload image",
                    "status": False,
                    "status_code": upload_response.status_code,
                    "response": upload_response.text,
                },
                status=upload_response.status_code,
            )

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
            return Response(
                {
                    "message": "Image posted successfully on LinkedIn",
                    "status": True,
                    "status_code": 200,
                    "response": final_post_response.json(),
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "message": "Failed to post image on LinkedIn",
                "status": False,
                "status_code": final_post_response.status_code,
                "response": final_post_response.json(),
            },
            status=final_post_response.status_code,
        )


class GetOrganizationsLinkedInView(APIView):
    def post(self, request):
        access_token = request.data.get("access_token")

        if not access_token:
            return Response(
                {
                    "message": "Access Token is required",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        orgs_url = f"{settings.LINKEDIN_API_URL}v2/organizationalEntityAcls"
        params = {
            "q": "roleAssignee",
            "role": "ADMINISTRATOR",
            "state": "APPROVED",
            "projection": "(elements*(*,organizationalTarget~(localizedName)))",
        }

        response = requests.get(orgs_url, headers=headers, params=params)

        if response.status_code != 200:
            return Response(
                {
                    "message": "Failed to fetch organizations from LinkedIn",
                    "status": False,
                    "status_code": response.status_code,
                    "response": response.json(),
                },
                status=response.status_code,
            )

        data = response.json()
        organizations = []
        for element in data.get("elements", []):
            org = element.get("organizationalTarget~", {})
            organizations.append(
                {
                    "urn": element.get("organizationalTarget"),
                    "name": org.get("localizedName"),
                }
            )

        return Response(
            {
                "message": "Organizations fetched successfully",
                "status": True,
                "status_code": 200,
                "response": organizations,
            },
            status=status.HTTP_200_OK,
        )


class VerifyTikTokView(APIView):
    def post(self, request):
        code = request.data.get("code", None)
        if not code:
            return Response(
                {
                    "message": "Please Provide me a code",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        url = f"{settings.TIKTOK_API_URL}oauth/token/"
        data = {
            "client_key": settings.TIKTOK_CLIENT_ID,
            "client_secret": settings.TIKTOK_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.TIKTOK_REDIRECT_URL,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        get_access_token = requests.post(url, data=data, headers=headers)
        if get_access_token.status_code not in [200, 201]:
            return Response(
                {
                    "message": "Access Token cannot be generated right now try again",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        access_token = get_access_token.json().get("access_token")
        if not access_token:
            return Response(
                {
                    "message": "Access Token cannot be generated right now try again",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        posts_content_path = os.path.join(settings.BASE_DIR, "tiktok.csv")
        Thread(
            target=start_uploading_on_tiktok, args=(posts_content_path, access_token)
        ).start()
        return Response(
            {
                "message": "Video Posting Started Successfullyy",
                "status": True,
                "status_code": 200,
                "response": None,
            },
            status=status.HTTP_200_OK,
        )


class UploadVideoTiktokView(APIView):
    def post(self, request):
        access_token = request.data.get("access_token", None)
        video_url = request.data.get("video_url", None)
        if not access_token or not video_url:
            return Response(
                {
                    "message": "Access Token and Video URL are required",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        video_path = download_video_from_url(video_url=video_url)
        if not video_path:
            return Response(
                {
                    "message": "Error Downloading the video",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        video_size = os.path.getsize(video_path)
        min_chunk = 5 * 1024 * 1024  # 5MB
        max_chunk = 64 * 1024 * 1024  # 64MB
        max_final_chunk = 128 * 1024 * 1024  # Final chunk can be up to 128MB
        max_chunks = 1000

        # Decide chunk size
        if video_size < min_chunk or video_size <= max_chunk:
            # Whole upload
            chunk_size = video_size
            total_chunk_count = 1
        else:
            # Use max 64MB chunks and ceil to avoid going over 1000 chunks
            chunk_size = min(max_chunk, math.ceil(video_size / max_chunks))
            total_chunk_count = math.floor(video_size / chunk_size)
            if video_size % chunk_size != 0:
                total_chunk_count += 1

        url = f"{settings.TIKTOK_API_URL}post/publish/creator_info/query/"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

        response = requests.post(url, headers=headers)
        if response.status_code not in [200, 201]:
            return Response(
                {
                    "message": "Error while fetching user info",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        creator_data = response.json().get("data")
        if not creator_data:
            return Response(
                {
                    "message": "No Creator Dta found",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        privacy_options = creator_data.get("privacy_level_options", ["SELF_ONLY"])
        comment_disabled = creator_data.get("comment_disabled", False)
        duet_disabled = creator_data.get("duet_disabled", False)
        stitch_disabled = creator_data.get("stitch_disabled", True)
        upload_video_url = f"{settings.TIKTOK_API_URL}post/publish/video/init/"
        post_video_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }
        post_video_data = {
            "post_info": {
                "title": "this will be a funny #cat video on your @tiktok #fyp",
                "privacy_level": "SELF_ONLY",
                "disable_duet": duet_disabled,
                "disable_comment": comment_disabled,
                "disable_stitch": stitch_disabled,
                # "video_cover_timestamp_ms": 1000
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
            return Response(
                {
                    "message": "Posting video Not Successsfull",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        post_video_response_data = post_video_response.json().get("data")
        if not post_video_response_data:
            return Response(
                {
                    "message": "Posting video is Not Successsfull as no publish url returned",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        url_for_video_upload = post_video_response_data.get("upload_url")
        with open(video_path, "rb") as f:
            print(
                f"Uploading {video_size} bytes in {total_chunk_count} chunks (chunk_size={chunk_size})"
            )
            for i in range(total_chunk_count):
                print(i)
                start_byte = i * chunk_size
                end_byte = min((i + 1) * chunk_size - 1, video_size - 1)
                f.seek(start_byte)
                chunk_data = f.read(end_byte - start_byte + 1)
                upload_video_headers = {
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(chunk_data)),
                    "Content-Range": f"bytes {start_byte}-{end_byte}/{video_size}",
                }
                try:
                    response_of_chunk_upload = requests.put(
                        url_for_video_upload,
                        headers=upload_video_headers,
                        data=chunk_data,
                        timeout=(10, 480),
                    )
                    if response_of_chunk_upload.status_code not in [200, 201]:
                        return Response(
                            {
                                "message": f"Failed to upload the {i} chunk of video",
                                "status": False,
                                "status_code": 400,
                                "response": response_of_chunk_upload.text,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                except Exception as e:
                    print(e)
                    return Response(
                        {
                            "message": f"Failed to upload the {i} chunk of video",
                            "status": False,
                            "status_code": 400,
                            "response": None,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        os.remove(video_path)
        return Response(
            {
                "message": "Video Posted. Please check your tiktok after a minute",
                "status": True,
                "status_code": 200,
                "response": None,
            },
            status=status.HTTP_200_OK,
        )
