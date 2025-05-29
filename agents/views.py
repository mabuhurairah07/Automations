from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from .models import UserCredits, Agents, UserAgent, UserAgentResponseData
from .utils import fire_and_forget
import threading
import requests
import uuid


class SignupView(APIView):
    def post(self, request):
        user_name = request.data.get("username", None)
        user_email = request.data.get("email", None)
        password = request.data.get("password", None)
        first_name = request.data.get("firstName", None)
        last_name = request.data.get("lastName", None)
        is_admin = request.data.get("is_admin", False)

        if not user_name:
            return Response(
                {
                    "message": "Please Provide a UserName",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if not user_email:
            return Response(
                {
                    "message": "Please Provide a EMail",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if not password:
            return Response(
                {
                    "message": "Please Provide a Password",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            user = User.objects.get(username=user_name)
            if user:
                return Response(
                    {
                        "message": "User Already Exists",
                        "status": False,
                        "status_code": 400,
                        "response": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except User.DoesNotExist:
            print("Going to create a new User")
        user = User.objects.create(username=user_name, email=user_email)
        user.set_password(password)
        user.first_name = first_name if first_name else ""
        user.last_name = last_name if last_name else ""
        user.is_staff = is_admin if is_admin else False
        user.save()
        if not user.is_staff:
            UserCredits.objects.create(user=user)
        return Response(
            {
                "message": "User Created Successfully",
                "status": True,
                "status_code": 201,
                "response": user.pk,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email", None)
        password = request.data.get("password", None)
        print(password)

        if not email:
            return Response(
                {
                    "message": "Please Provide an Email",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if not password:
            return Response(
                {
                    "message": "Please Provide a Password",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {
                    "message": "No User Found",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if not user.check_password(password):
            return Response(
                {
                    "message": "Password Authentication Failed",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "message": "User Logged in Successfully",
                "status": True,
                "status_code": 200,
                "response": user.pk,
            },
            status=status.HTTP_200_OK,
        )


class AgentsView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id", None)
        agent_name = request.data.get("agent_name", None)
        agent_url = request.data.get("agent_url", None)
        if not user_id:
            return Response(
                {
                    "message": "Please Provide a User Id to continue",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if not agent_name:
            return Response(
                {
                    "message": "Please Provide an agent name",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if not agent_url:
            return Response(
                {
                    "message": "Please Provide an agent url",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        user = User.objects.filter(pk=user_id, is_staff=True).first()
        if not user:
            return Response(
                {
                    "message": "No Admin Found. Please Use an Admin account",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        agent = Agents.objects.create(
            name=agent_name, starting_url=agent_url, created_by=user
        )
        return Response(
            {
                "message": "Agent created successfully",
                "status": True,
                "status_code": 200,
                "response": agent.pk,
            },
            status=status.HTTP_200_OK,
        )

    def get(self, request):

        agents = Agents.objects.all()
        rtn_array = [
            {
                "agent_id": agent.pk,
                "agent_name": agent.name,
                "agent_url": agent.starting_url,
                "created_at": agent.created_at,
                "updated_at": agent.updated_at,
            }
            for agent in agents
        ]
        return Response(
            {
                "message": "Agents Fetched Successfully",
                "status": True,
                "status_code": 201,
                "response": rtn_array,
            },
            status=status.HTTP_201_CREATED,
        )


class UserAgentsView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id", None)
        agent_id = request.data.get("agent_id", None)
        request_data = request.data.get("data_to_send", None)
        if not user_id:
            return Response(
                {
                    "message": "Please Provide a User Id to continue",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if not agent_id:
            return Response(
                {
                    "message": "Please Provide an Agent Id to continue",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response(
                {
                    "message": "No User Found.",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        agent = Agents.objects.filter(pk=agent_id).first()
        if not agent:
            return Response(
                {
                    "message": "No agent found",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        credits = (
            UserCredits.objects.filter(user=user).first() if not user.is_staff else None
        )
        user_agent = UserAgent.objects.create(
            user=user, agent=agent, request_data=request_data
        )
        if request_data:
            request_data["user_agent_id"] = user_agent.user_agent_id
            request_data["webhook_url"] = (
                "https://6673-188-52-243-222.ngrok-free.app/services/n8n_webhook/"
            )
            request_data["sessionId"] = str(uuid.uuid4())
        else:
            request_data = {
                "user_agent_id": user_agent.user_agent_id,
                "webhook_url": "https://6673-188-52-243-222.ngrok-free.app/services/n8n_webhook/",
                "sessionId": str(uuid.uuid4()),
            }
        if credits and credits.total_credits <= credits.used_credits:
            return Response(
                {
                    "message": "No Credits Left Please buy some",
                    "status": False,
                    "status_code": 400,
                    "response": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        threading.Thread(
            target=fire_and_forget, args=(agent.starting_url, request_data)
        ).start()
        if credits:
            credits.used_credits += 1
            credits.save()
        return Response(
            {
                "message": "Your Request has been submitted successfully. Please wait for response",
                "status": True,
                "status_code": 200,
                "response": user_agent.pk,
            },
            status=status.HTTP_200_OK,
        )

    def get(self, request):
        user_id = request.GET.get("user_id", None)
        user_agent_id = request.GET.get("user_agent_id", None)
        if not user_id:
            return Response(
                {
                    "message": "No User ID provided",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if user_agent_id:
            user_agent = UserAgent.objects.filter(pk=user_agent_id).first()
            if not user_agent:
                return Response(
                    {
                        "message": f"No User Agent Found with ID {user_agent_id}",
                        "status": False,
                        "status_code": 404,
                        "response": None,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            agent_responses = UserAgentResponseData.objects.filter(
                user_agent=user_agent
            )
            rtn_array = {
                "agent_id": user_agent.user_agent_id,
                "request_data": user_agent.request_data,
                "response_data": [
                    agent_response.response_data for agent_response in agent_responses
                ],
            }
            return Response(
                {
                    "message": "Data Fetched SuccessFully",
                    "status": True,
                    "status_code": 200,
                    "response": rtn_array,
                },
                status=status.HTTP_200_OK,
            )
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response(
                {
                    "message": "No User Found",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        user_agents = UserAgent.objects.filter(user=user)
        if not user_agents:
            return Response(
                {
                    "message": f"No User Agent Found associated with user {user.username}",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        rtn_array = [
            {
                "agent_id": user_agent.user_agent_id,
                "used_agent_name": user_agent.agent.name,
                "request_data": user_agent.request_data,
                "created_at": user_agent.created_at,
                "updated_at": user_agent.updated_at,
            }
            for user_agent in user_agents
        ]
        return Response(
            {
                "message": "User Agents Fetched SuccessFully",
                "status": True,
                "status_code": 200,
                "response": rtn_array,
            },
            status=status.HTTP_200_OK,
        )


@api_view(["POST"])
def recieve_data_from_n8n_webhook(request):
    response_data = request.data.get("response_data", None)
    print(response_data)
    if not response_data:
        return Response(
            {
                "message": "No Response Data given",
                "status": False,
                "status_code": 404,
                "response": None,
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    user_agent_id = response_data.get("user_agent_id", None)
    print(user_agent_id)
    if not user_agent_id:
        return Response(
            {
                "message": "No Agent ID provided",
                "status": False,
                "status_code": 404,
                "response": None,
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    user_agent = UserAgent.objects.filter(user_agent_id=user_agent_id).first()
    if not user_agent:
        return Response(
            {
                "message": "No Agent Found with this ID",
                "status": False,
                "status_code": 404,
                "response": None,
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    del response_data["user_agent_id"]
    save_message = response_data["message"]
    UserAgentResponseData.objects.create(
        user_agent=user_agent, response_data=save_message
    )
    return Response(
        {
            "message": "Data Saved Successfully",
            "status": True,
            "status_code": 200,
            "response": None,
        },
        status=status.HTTP_200_OK,
    )


class ChatAgentsView(APIView):
    def post(self, request):
        agent_id = request.data.get("agent_id", None)
        request_data = request.data.get("user_data", None)
        history = request.data.get("history", None)
        print(history)
        if not agent_id:
            return Response(
                {
                    "message": "Please Provide an Agent Id to continue",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        agent = Agents.objects.filter(pk=agent_id).first()
        if not agent:
            return Response(
                {
                    "message": "No agent found",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        data = {
            "user_message": request_data,
            "history": history,
            "sessionId": str(uuid.uuid4()),
        }
        try:
            response = requests.post(
                agent.starting_url,
                json=data,
            )
        except Exception as e:
            print(e)
            response = "There was an error communicating with Agent"
        if not response:
            return Response(
                {
                    "message": "No agent found",
                    "status": False,
                    "status_code": 404,
                    "response": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "message": "Your Request has been submitted successfully. Please wait for response",
                "status": True,
                "status_code": 200,
                "response": response,
            },
            status=status.HTTP_200_OK,
        )
