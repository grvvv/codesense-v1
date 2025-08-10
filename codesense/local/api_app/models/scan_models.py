# scanner/models/scan_model.py

from bson import ObjectId
from datetime import datetime
from common.db import MongoDBClient

class ScanModel:
    collection = MongoDBClient.get_database()["scans"]

    @staticmethod
    def serialize(scan):
        if not scan:
            return None
        return {
            "id": str(scan["_id"]),
            "project_id": str(scan["project_id"]),
            "scan_name": scan.get("scan_name", ""),
            "status": scan.get("status", "queued"),
            "created_at": scan.get("created_at"),
            "triggered_by": str(scan.get("triggered_by", "")),
            "total_files": scan.get("total_files", 0),
            "files_scanned": scan.get("files_scanned", 0),
            "findings": scan.get("findings", 0),
            "end_time": scan.get("end_time"),
        }

    @classmethod
    def create(cls, data: dict):
        """
        Create a new scan document.
        Expects: project_id, scan_name, triggered_by (optional)
        """
        data["project_id"] = ObjectId(data["project_id"]) if isinstance(data.get("project_id"), str) else data["project_id"]
        if "triggered_by" in data:
            data["triggered_by"] = ObjectId(data["triggered_by"]) if isinstance(data["triggered_by"], str) else data["triggered_by"]
        data["created_at"] = datetime.utcnow()
        data["status"] = "queued"
        data["deleted"] = False
        data["total_files"] = 0
        data["files_scanned"] = 0
        data["findings"] = 0
        data["end_time"] = None

        result = cls.collection.insert_one(data)
        return cls.find_by_id(result.inserted_id)

    @classmethod
    def update_status(cls, scan_id: str, new_status: str):
        """
        Update scan status to one of: queued, in_progress, completed, failed
        """
        cls.collection.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": {"status": new_status}}
        )
        return cls.find_by_id(scan_id)

    @classmethod
    def update_progress(cls, scan_id: str, **kwargs):
        """
        Update any subset of: total_files, files_scanned, findings, end_time, status
        Example: update_progress(scan_id, files_scanned=3, findings=7)
        """
        update_fields = {}
        for key in ["total_files", "files_scanned", "findings", "end_time", "status"]:
            if key in kwargs:
                update_fields[key] = kwargs[key]

        if update_fields:
            cls.collection.update_one(
                {"_id": ObjectId(scan_id)},
                {"$set": update_fields}
            )

        return cls.find_by_id(scan_id)

    @classmethod
    def find_by_id(cls, scan_id: str):
        scan = cls.collection.find_one({"_id": ObjectId(scan_id)})
        return cls.serialize(scan)

    @classmethod
    def find_by_project(cls, project_id: str, page=1, limit=10):
        skip = (page - 1) * limit
        cursor = cls.collection.find({"project_id": ObjectId(project_id)}).skip(skip).limit(limit)
        scans =  [cls.serialize(doc) for doc in cursor]

        total = cls.collection.count_documents({"project_id": ObjectId(project_id)})
        return {
            "scans": scans,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        }

    @classmethod
    def delete(cls, scan_id: str):
        result = cls.collection.delete_one({"_id": ObjectId(scan_id)})
        return result.deleted_count == 1
