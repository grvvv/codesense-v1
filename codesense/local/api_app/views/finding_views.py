# projects/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId

from ..models.finding_models import FindingModel

class FindingListCreateView(APIView):
    def get(self, request, scan_id):
        try:     
            findings = FindingModel.find_by_scan(scan_id=scan_id)
            if not findings:
                return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({ "result": findings })
        except Exception as e:
            return Response({ "error": e }, status=status.HTTP_400_BAD_REQUEST)

class FindingDetailView(APIView):
    def get(self, request, finding_id):
        finding = FindingModel.find_by_id(finding_id=finding_id)
        if not finding:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({ "result": finding })

    # def patch(self, request, project_id):
    #     serializer = ProjectUpdateSerializer(data=request.data)
    #     if serializer.is_valid():
    #         updated = FindingModel.update(project_id, serializer.validated_data)
    #         return Response(updated)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, project_id):
        FindingModel.soft_delete(project_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
