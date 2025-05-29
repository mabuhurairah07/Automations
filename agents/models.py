from django.db import models
from django.contrib.auth.models import User
import uuid


class Agents(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    starting_url = models.CharField(max_length=500, null=False, blank=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserAgent(models.Model):
    user_agent_id = models.CharField(
        max_length=200, default=str(uuid.uuid4()), unique=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    agent = models.ForeignKey(Agents, on_delete=models.CASCADE, null=False, blank=False)
    request_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserAgentResponseData(models.Model):
    user_agent = models.ForeignKey(UserAgent, on_delete=models.CASCADE)
    response_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserCredits(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_credits = models.IntegerField(null=False, blank=False, default=10)
    used_credits = models.IntegerField(null=False, blank=False, default=0)
