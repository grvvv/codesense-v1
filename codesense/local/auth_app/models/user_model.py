# local/auth_app/models/user_model.py

from bson import ObjectId
from datetime import datetime, timezone
from common.db import MongoDBClient

class UserModel:
    collection = MongoDBClient.get_database()["users"]

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
            "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
            "updated_at": user["updated_at"].isoformat() if user.get("updated_at") else None,
        }

    @staticmethod
    def find_all(page=1, limit=10):
        try:
            skip = (page - 1) * limit
            users_cursor = UserModel.collection.find({ "deleted": False }).skip(skip).limit(limit)
            users = [UserModel.serialize_user(u) for u in users_cursor]

            total = UserModel.collection.count_documents({"deleted": False})
            return {
                "users": users,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "pages": (total + limit - 1) // limit
                }
            }
        except:
            return {
                "error": "Internal Server Error"
            }
    
    @staticmethod
    def find_by_email(email: str):
        user = UserModel.collection.find_one({"email": email, "deleted": False })
        if not user:
            return None
        return user

    @staticmethod
    def find_by_id(user_id: str):
        try:
            user = UserModel.collection.find_one({"_id": ObjectId(user_id), "deleted": False})
            return UserModel.serialize_user(user)
        except Exception:
            return None

    @staticmethod
    def create_user(email: str, hashed_password: str, name: str, company: str = None, role: str = "User", deleted: bool = False):
        now = datetime.now(timezone.utc)
        user_data = {
            "email": email,
            "password": hashed_password,
            "name": name,
            "company": company,
            "role": role,
            "deleted": deleted,
            "created_at": now,
            "updated_at": now,
        }
        result = UserModel.collection.insert_one(user_data)
        return UserModel.find_by_id(result.inserted_id)

    @staticmethod
    def update_user(user_id: str, update_data: dict):
        update_data["updated_at"] = datetime.now(timezone.utc)
        UserModel.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return UserModel.find_by_id(user_id)

    @staticmethod
    def delete_user(user_id: str):
        return UserModel.collection.delete_one({"_id": ObjectId(user_id)})

    @staticmethod
    def exists(email: str) -> bool:
        return UserModel.collection.count_documents({"email": email}) > 0
