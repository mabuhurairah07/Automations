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
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("agents/", views.AgentsView.as_view(), name="agents"),
    path("user_agents/", views.UserAgentsView.as_view(), name="user_agents"),
    path("chat_agents/", views.ChatAgentsView.as_view(), name="chat_agents"),
    path("n8n_webhook/", views.recieve_data_from_n8n_webhook, name="n8n_webhook"),
]
