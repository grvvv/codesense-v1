from datetime import datetime, timedelta
from local.auth_app.permissions.decorators import require_authentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.db import MongoDBClient

class DashboardView(APIView):
    @require_authentication()
    def get(self, request):
        try:
            db = MongoDBClient.get_database()

            # Top counts (collections may not exist yet)
            total_users = db.users.count_documents({"deleted": False}) if "users" in db.list_collection_names() else 0
            total_projects = db.projects.count_documents({"deleted": False}) if "projects" in db.list_collection_names() else 0
            total_scans = db.scans.count_documents({}) if "scans" in db.list_collection_names() else 0
            total_findings = db.findings.count_documents({"deleted": False}) if "findings" in db.list_collection_names() else 0

            # System status pipeline
            system_status_pipeline = [
                {
                    '$facet': {
                        'status_counts': [
                            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
                        ],
                        'total_scans': [{'$count': 'total'}]
                    }
                },
                {
                    '$project': {
                        'counts': {
                            '$arrayToObject': {
                                '$map': {
                                    'input': '$status_counts',
                                    'as': 'item',
                                    'in': {'k': '$$item._id', 'v': '$$item.count'}
                                }
                            }
                        },
                        'total_scans': {'$arrayElemAt': ['$total_scans.total', 0]}
                    }
                }
            ]

            # Severity pipeline
            severity_pipeline = [
                {'$match': {'deleted': False}},
                {'$group': {'_id': '$severity', 'count': {'$sum': 1}}},
                {'$group': {'_id': None, 'severities': {'$push': {'k': '$_id', 'v': '$count'}}}},
                {
                    '$project': {
                        '_id': 0,
                        'counts': {
                            '$mergeObjects': [
                                {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                                {'$arrayToObject': '$severities'}
                            ]
                        }
                    }
                }
            ]

            # Run safely (empty fallback)
            system_status = list(db.scans.aggregate(system_status_pipeline)) if "scans" in db.list_collection_names() else []
            findings_chart = list(db.findings.aggregate(severity_pipeline)) if "findings" in db.list_collection_names() else []

            system_status_result = system_status[0] if system_status else {"counts": {}, "total_scans": 0}
            findings_chart_result = findings_chart[0]["counts"] if findings_chart else {"critical": 0, "high": 0, "medium": 0, "low": 0}

            response_data = {
                "top_counts": {
                    "users": total_users,
                    "projects": total_projects,
                    "scans": total_scans,
                    "findings": total_findings,
                },
                "system_status": system_status_result,
                "count_by_severity": findings_chart_result,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
