"""
URL configuration for talkingagents project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from . import views

urlpatterns = [
    path(
        "linkedin_verify/", views.VerifyLinkedInView.as_view(), name="linkedin_verify"
    ),
    path("tiktok_verify/", views.VerifyTikTokView.as_view(), name="tiktok_verify"),
    path(
        "linkedin_pages/",
        views.GetOrganizationsLinkedInView.as_view(),
        name="linkedin_pages",
    ),
    path(
        "upload_on_tiktok/",
        views.UploadVideoTiktokView.as_view(),
        name="upload_on_tiktok",
    ),
    path(
        "create_linkedin_post/",
        views.CreatePostLinkedIn.as_view(),
        name="post_creation",
    ),
]
