# projects/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework import status
from local.auth_app.permissions.decorators import require_permission
from openpyxl import Workbook
from bson import ObjectId

from ..models.finding_models import FindingModel

class FindingListCreateView(APIView):
    @require_permission("view_findings")
    def get(self, request, scan_id):
        try:     
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 10))

            findings = FindingModel.find_by_scan(scan_id=scan_id, page=page, limit=limit)
            if not findings:
                return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(findings, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({ "error": e }, status=status.HTTP_400_BAD_REQUEST)

class ExportFindingView(APIView):
    @require_permission("view_findings")
    def get(self, request, scan_id):
        try:
            findings = FindingModel.find_all_by_scan(scan_id=scan_id)
            if not findings:
                return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Create Excel workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Findings"

            # Write header row
            headers = ["Sr No", "Title", "CWE", "Severity", "CVSS Score", "Description", "File", "Reference", "Created At"]
            ws.append(headers)

            for index, f in enumerate(findings):
                ws.append([
                    index + 1,
                    f.get("title", ""),
                    f.get("cwe", ""),
                    f.get("severity", ""),
                    f.get("cvss_score", ""),
                    f.get("description", ""),
                    f.get("file_path", ""),
                    f.get("reference", ""),
                    f.get("created_at", "").strftime("%Y-%m-%d %H:%M:%S") if f.get("created_at") else ""
                ])
            
            # Create HTTP response
            response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = f'attachment; filename="scan_{scan_id}_findings.xlsx"'
            
            # Save workbook into response
            wb.save(response)
            
            return response
        except Exception as e:
            return Response({ "error": e }, status=status.HTTP_400_BAD_REQUEST)

class FindingDetailView(APIView):
    @require_permission("view_findings")
    def get(self, request, finding_id):
        finding = FindingModel.find_by_id(finding_id=finding_id)
        if not finding:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(finding, status=status.HTTP_200_OK)
    
    @require_permission("validate_finding")
    def patch(self, request, finding_id):
        updated_finding = FindingModel.toggle_approved(finding_id=finding_id)
        if not updated_finding:
            return Response({"error": "Not found or not updated"}, status=status.HTTP_404_NOT_FOUND)
        return Response(updated_finding, status=status.HTTP_200_OK)

    @require_permission("delete_finding")
    def delete(self, request, project_id):
        FindingModel.soft_delete(project_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
