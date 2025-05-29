from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
import requests
import talkingagents.settings as settings
import os
import math


# Create your views here.


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
        return Response(
            {
                "message": "Access Token Generated Successfully",
                "status": True,
                "status_code": 200,
                "response": response_tokens.get("access_token"),
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
        return Response(
            {
                "message": "Access Token Generated Successfully",
                "status": True,
                "status_code": 200,
                "response": access_token,
            },
            status=status.HTTP_200_OK,
        )


class UploadVideoTiktokView(APIView):
    def post(self, request):
        access_token = request.data.get("access_token", None)
        video_path = request.data.get("video_path", None)
        video_path = (
            "/root/SA/TalkingAgents/talkingagents/855289-hd_1920_1080_25fps.mp4"
        )
        if not access_token or not video_path:
            return Response(
                {
                    "message": "Access Token and Video URL are required",
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
                        data=f,
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

        return Response(
            {
                "message": "Video Posted. Please check your tiktok after a minute",
                "status": True,
                "status_code": 200,
                "response": None,
            },
            status=status.HTTP_200_OK,
        )
