from datetime import datetime, timedelta
from local.auth_app.permissions.decorators import require_permission, require_role
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.db import MongoDBClient

class DashboardView(APIView):
    @require_role("Admin")
    def get(self, request):
        try:     
            db = MongoDBClient.get_database()
            total_users = db.users.count_documents({"deleted": False})
            total_projects = db.projects.count_documents({"deleted": False})
            total_scans = db.scans.count_documents({})
            total_findings = db.findings.count_documents({"deleted": False})

            active_scans = db.scans.count_documents({"status": "in_progress"})
            active_percent = (active_scans / total_scans * 100) if total_scans else 0
            remaining_percent = 100 - active_percent

            # Findings by severity per day (last 7 days)
            last_7_days = datetime.utcnow() - timedelta(days=7)
            pipeline = [
                {"$match": {
                    "deleted": False,
                    "created_at": {"$gte": last_7_days}
                }},
                {"$project": {
                    "severity": 1,
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}
                }},
                {"$group": {
                    "_id": {"date": "$date", "severity": "$severity"},
                    "count": {"$sum": 1}
                }},
                {"$group": {
                    "_id": "$_id.date",
                    "severities": {
                        "$push": {
                            "severity": "$_id.severity",
                            "count": "$count"
                        }
                    }
                }},
                {"$sort": {"_id": 1}}
            ]
            severity_by_date_raw = list(db.findings.aggregate(pipeline))

            # Format for frontend
            findings_trend = []
            for entry in severity_by_date_raw:
                row = {"date": entry["_id"], "high": 0, "medium": 0, "low": 0}
                for sev in entry["severities"]:
                    row[sev["severity"].lower()] = sev["count"]
                findings_trend.append(row)

            return Response({
                "top_counts": {
                    "users": total_users,
                    "projects": total_projects,
                    "scans": total_scans,
                    "findings": total_findings,
                },
                "system_status": {
                    "active_percent": round(active_percent),
                    "remaining_percent": round(remaining_percent),
                },
                "findings_trend": findings_trend
            })
        except Exception as e:
            return Response({ "error": e }, status=status.HTTP_400_BAD_REQUEST) 
        
