# local/auth_app/models/user_model.py

from bson import ObjectId
from datetime import datetime
from common.db import MongoDBClient


class UserModel:
    @staticmethod
    def _get_collection():
        db = MongoDBClient.get_database()
        return db["users"]

    @staticmethod
    def serialize_user(user):
        if not user:
            return None
        return {
            "id": str(user.get("_id")),
            "email": user.get("email"),
            "name": user.get("name"),
            "company": user.get("company"),
            "role": user.get("role", "User"),
            "deleted": user.get("deleted", True),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at"),
        }

    @staticmethod
    def find_by_email(email: str):
        collection = UserModel._get_collection()
        user = collection.find_one({"email": email})
        return user

    @staticmethod
    def find_by_id(user_id: str):
        try:
            collection = UserModel._get_collection()
            user = collection.find_one({"_id": ObjectId(user_id)})
            return UserModel.serialize_user(user)
        except Exception:
            return None

    @staticmethod
    def create_user(email: str, hashed_password: str, name: str, company: str = None, role: str = None):
        now = datetime.utcnow()
        collection = UserModel._get_collection()
        user_data = {
            "email": email,
            "password": hashed_password,
            "name": name,
            "company": company,
            "role": role,
            "deleted": True,
            "created_at": now,
            "updated_at": now,
        }
        result = collection.insert_one(user_data)
        return UserModel.find_by_id(result.inserted_id)

    @staticmethod
    def update_user(user_id: str, update_data: dict):
        update_data["updated_at"] = datetime.utcnow()
        collection = UserModel._get_collection()
        collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return UserModel.find_by_id(user_id)

    @staticmethod
    def delete_user(user_id: str):
        collection = UserModel._get_collection()
        return collection.delete_one({"_id": ObjectId(user_id)})

    @staticmethod
    def exists(email: str) -> bool:
        collection = UserModel._get_collection()
        return collection.count_documents({"email": email}) > 0
