from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Users
from .serializers import UserSerializer
import re


@csrf_exempt
@api_view(["POST"])
def signup(request):
    data = request.data
    required_fields = ["first_name", "last_name", "email", "password"]
    for field in required_fields:
        if field not in data or not data[field]:
            return Response(
                {"error": f"{field} is required."}, status=status.HTTP_400_BAD_REQUEST
            )

    # Email format check
    if not is_valid_email(data["email"]):
        return Response(
            {"error": "Invalid email format."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Password strength check
    if not is_strong_password(data["password"]):
        return Response(
            {
                "error": "Password is not strong enough. Must be >=6 chars, with upper, lower, and digit."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Use the custom manager on your Users model
        user = Users.objects.create_user(
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            password=data["password"],
            transfer_type=data.get("transfer_type"),
        )
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current_password = request.data.get("current_password")
    new_password = request.data.get("new_password")

    # 1. Check current password
    if not user.check_password(current_password):
        return Response(
            {"error": "Current password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 2. Validate new password
    if not is_strong_password(new_password):
        return Response(
            {
                "error": "New password is not strong enough. Must be >=6 chars, with upper, lower, and digit."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 3. Set the new password
    user.set_password(new_password)
    user.save()

    return Response(
        {"message": "Password changed successfully!"}, status=status.HTTP_200_OK
    )


def test_api(request):
    return JsonResponse({"message": "Backend is working!"})


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Customize JWT response if needed"""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["first_name"] = self.user.first_name
        data["last_name"] = self.user.last_name
        return data  # Includes first_name and last_name in the token response for extra validation


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        data = request.data

        # If user is trying to change email, validate
        if "email" in data:
            new_email = data["email"].strip()
            if not is_valid_email(new_email):
                return Response(
                    {"error": "Invalid email format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # If email is valid, check for uniqueness (if needed)
            # if Users.objects.exclude(pk=user.pk).filter(email=new_email).exists():
            #     return Response({"error": "Email already taken."}, status=400)
            user.email = new_email

        # If user wants to update other fields:
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.transfer_type = data.get("transfer_type", user.transfer_type)

        user.save()

        serializer = UserSerializer(user)
        return Response(serializer.data, status=200)


def is_valid_email(email: str) -> bool:
    """Simple regex-based check for email format."""
    pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return bool(re.match(pattern, email))


def is_strong_password(password: str) -> bool:
    """
    Check if `password` meets your policy:
    - Length >= 6
    - Has at least one uppercase, one lowercase, one digit
    """
    if len(password) < 6:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True
