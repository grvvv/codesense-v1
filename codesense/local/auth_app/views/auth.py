# local/auth_app/views/auth.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from local.auth_app.serializers.user_serializer import RegisterUserSerializer, LoginSerializer
from local.auth_app.models.user_model import UserModel
from local.auth_app.utils.password import hash_password, verify_password
from local.auth_app.utils.jwt import generate_token
from local.auth_app.permissions.decorators import require_permission, require_role

class RegisterView(APIView):
    @require_role("Admin")
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        if UserModel.find_by_email(data["email"]):
            return Response({"detail": "Email already registered"}, status=400)

        user = UserModel.create_user(
            email=data["email"],
            hashed_password=hash_password(data["password"]),
            name=data["name"],
            company=data["company"],
            role=data["role"]
        )
        return Response(user, status=201)


class LoginView(APIView):
    def post(self, request):
        print(request.user)
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = UserModel.find_by_email(data["email"])

        if not user or not verify_password(data["password"], user["password"]):
            return Response({"detail": "Invalid credentials"}, status=401)

        token = generate_token({
            "user_id": str(user["_id"]), 
            "email": user["email"],
            "role": user["role"],
            "name": user["name"]
        })
        return Response({"token": token}, status=200)
