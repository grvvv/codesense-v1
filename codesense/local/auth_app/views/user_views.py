from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from local.auth_app.serializers.user_serializer import RegisterUserSerializer, UpdateUserSerializer
from local.auth_app.models.user_model import UserModel
from local.auth_app.permissions.decorators import require_permission, require_role, require_authentication
from local.auth_app.utils.password import hash_password, verify_password

class ProfileView(APIView):
    @require_authentication()
    def get(self, request):
        user = request.user
        user_id = user.get("id", "")
        
        if not user_id:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

        user = UserModel.find_by_id(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(user , status=status.HTTP_200_OK)

class FetchUserDetails(APIView):
    @require_role("Admin")
    def get(self, request, user_id):
        if not user_id:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

        user = UserModel.find_by_id(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(user , status=status.HTTP_200_OK)

class UserModuleView(APIView):
    @require_role("Admin")
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        if UserModel.find_by_email(data["email"]):
            return Response({"detail": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

        user = UserModel.create_user(
            email=data["email"],
            hashed_password=hash_password(data["password"]),
            name=data["name"],
            company=data["company"],
            role=data["role"],
        )
        return Response(user, status=status.HTTP_201_CREATED)
    
    @require_role("Admin")
    def patch(self, request, user_id):
        serializer = UpdateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if not UserModel.find_by_id(user_id=user_id):
            return Response({"detail": "User doesn't exists"}, status=status.HTTP_404_NOT_FOUND)

        data = serializer.validated_data
        user = UserModel.update_user(
            user_id=user_id,
            update_data=data
        )
        return Response(user, status=status.HTTP_202_ACCEPTED)
    
    @require_role("Admin")
    def delete(self, request, user_id):
        if not UserModel.find_by_id(user_id=user_id):
            return Response({"detail": "User doesn't exists"}, status=status.HTTP_404_NOT_FOUND)

        UserModel.update_user(
            user_id=user_id,
            update_data={"deleted": True}
        )
        return Response({ "detail": "User Deleted Successfully" }, status=status.HTTP_202_ACCEPTED)
    
    @require_role("Admin")
    def get(self, request):
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))

        all_users = UserModel.find_all(page=page, limit=limit)
        return Response(all_users, status=status.HTTP_200_OK)


