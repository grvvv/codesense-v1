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
            total_users = db.users.count_documents({"deleted": False})
            total_projects = db.projects.count_documents({"deleted": False})
            total_scans = db.scans.count_documents({})
            total_findings = db.findings.count_documents({"deleted": False})

            system_status_pipeline = [
                {
                    '$facet': {
                        'status_counts': [
                            {
                                '$group': {
                                    '_id': '$status', 
                                    'count': {
                                        '$sum': 1
                                    }
                                }
                            }
                        ], 
                        'total_scans': [
                            {
                                '$count': 'total'
                            }
                        ]
                    }
                }, {
                    '$project': {
                        'counts': {
                            '$arrayToObject': {
                                '$map': {
                                    'input': '$status_counts', 
                                    'as': 'item', 
                                    'in': {
                                        'k': '$$item._id', 
                                        'v': '$$item.count'
                                    }
                                }
                            }
                        }, 
                        'total_scans': {
                            '$arrayElemAt': [
                                '$total_scans.total', 0
                            ]
                        }
                    }
                }
            ]

            severity_pipeline = [
                {
                    "$match": {
                        "deleted": False  # optional filter
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "severity": "$severity",
                            "status": "$status"
                        },
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$group": {
                        "_id": "$_id.status",
                        "severities": {
                            "$push": {
                                "k": "$_id.severity",
                                "v": "$count"
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "status": "$_id",
                        "counts": {
                            "$mergeObjects": [
                                {"critical": 0, "high": 0, "medium": 0, "low": 0},
                                {"$arrayToObject": "$severities"}
                            ]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "data": {
                            "$push": {
                                "k": "$status",
                                "v": "$counts"
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "result": { "$arrayToObject": "$data" }
                    }
                }
            ]

            system_status = list(db.scans.aggregate(system_status_pipeline))
            findings_chart = list(db.findings.aggregate(severity_pipeline))

            return Response({
                "top_counts": {
                    "users": total_users,
                    "projects": total_projects,
                    "scans": total_scans,
                    "findings": total_findings,
                },
                "system_status": system_status[0],
                "count_by_severity": findings_chart[0]["result"]
            })
        except Exception as e:
            return Response({ "error": e }, status=status.HTTP_400_BAD_REQUEST) 
        
