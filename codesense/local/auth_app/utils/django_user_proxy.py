class AuthenticatedUser:
    def __init__(self, payload):
        self.id = payload.get("user_id")
        self.email = payload.get("email")
        self.role = payload.get("role")
        self._payload = payload

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True  # or make dynamic if stored in DB

    def to_dict(self):
        return self._payload

class AnonymousUser:
    is_authenticated = False
    is_active = False
