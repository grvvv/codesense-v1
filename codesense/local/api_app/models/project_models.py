# projects/models.py
from bson import ObjectId
from datetime import datetime
from common.db import MongoDBClient

class ProjectModel:
    collection = MongoDBClient.get_database()["projects"]

    @staticmethod
    def serialize(project):
        if not project:
            return None
        return {
            "id": str(project["_id"]),
            "name": project["name"],
            "preset": project.get("preset", ""),
            "description": project.get("description", ""),
            "created_by": str(project["created_by"]),
            "created_at": project["created_at"],
            "deleted": project.get("deleted", True)
        }

    @classmethod
    def create(cls, data):
        data["created_at"] = datetime.utcnow()
        data["deleted"] = True
        result = cls.collection.insert_one(data)
        return cls.serialize(cls.collection.find_one({"_id": result.inserted_id}))

    @classmethod
    def find_all(cls):
        return [cls.serialize(doc) for doc in cls.collection.find({"deleted": True})]

    @classmethod
    def find_by_id(cls, project_id):
        return cls.serialize(cls.collection.find_one({"_id": ObjectId(project_id)}))

    @classmethod
    def update(cls, project_id, data):
        cls.collection.update_one({"_id": ObjectId(project_id)}, {"$set": data})
        return cls.find_by_id(project_id)

    @classmethod
    def soft_delete(cls, project_id):
        cls.collection.update_one({"_id": ObjectId(project_id)}, {"$set": {"deleted": False}})
        return True
