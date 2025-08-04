# local/auth_app/models/permission_model.py

from datetime import datetime
from common.db import MongoDBClient

class PermissionModel:
    collection = MongoDBClient.get_database()["permissions"]

    @staticmethod
    def get_permissions_for_role(role: str) -> dict:
        if role == "admin":
            # Grant all possible permissions
            return {key: True for key in PermissionModel.get_all_permission_keys()}

        doc = PermissionModel.collection.find_one({"role": role})
        return doc.get("permissions", {}) if doc else {}

    @staticmethod
    def set_permissions_for_role(role: str, permissions: dict):
        now = datetime.utcnow()
        PermissionModel.collection.update_one(
            {"role": role},
            {"$set": {
                "permissions": permissions,
                "updated_at": now
            }},
            upsert=True
        )

    @staticmethod
    def get_all_permission_keys() -> list:
        """Return all supported permission keys."""
        return [
            "create_project",
            "delete_project",
            "update_project",
            "view_reports",
            "generate_report",
            "create_scan",
            "update_scan",
            "delete_scan",
            "create_finding",
            "approve_finding",
            "reopen_finding",
            "request_reassessment",
            "comment_on_finding",
            "upload_evidence",
            "download_report"
        ]
