from models.permission_model import PermissionModel

def has_permission(user: dict, permission: str) -> bool:
    role = user.get("role")
    if not role:
        return False

    if role == "Admin":
        return True  # Admin bypass

    role_permissions = PermissionModel.get_permissions(role)
    return role_permissions.get(permission, False)