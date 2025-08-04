# projects/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId

from ..models.project_models import ProjectModel
from ..serializers.project_serializers import ProjectCreateSerializer, ProjectUpdateSerializer

class ProjectListCreateView(APIView):
    def get(self, request):
        projects = ProjectModel.find_all()
        return Response({"result": projects})

    def post(self, request):
        serializer = ProjectCreateSerializer(data=request.data)
        if serializer.is_valid():
            user_id = request.user.id  # Assuming user is authenticated
            project = ProjectModel.create({**serializer.validated_data, "created_by": ObjectId(user_id)})
            return Response({ "result" : project }, status=status.HTTP_201_CREATED)
        return Response({ "error": serializer.errors }, status=status.HTTP_400_BAD_REQUEST)

class ProjectDetailView(APIView):
    def get(self, request, project_id):
        project = ProjectModel.find_by_id(project_id)
        if not project:
            return Response({"error": "Project Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({ "result": project })

    def patch(self, request, project_id):
        project = ProjectModel.find_by_id(project_id)
        if not project:
            return Response({"error": "Project Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProjectUpdateSerializer(data=request.data)
        if serializer.is_valid():
            updated = ProjectModel.update(project_id, serializer.validated_data)
            return Response({ "result": updated })
        return Response({ "error": serializer.errors }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, project_id):
        ProjectModel.soft_delete(project_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
