from django.urls import path
from .views.auth import LoginView, GetPermissionsView, SetPermissionsView
from .views.user import ProfileView, UserModuleView

urlpatterns = [
    path('register/', UserModuleView.as_view(), name="create_user"),
    path('login/', LoginView.as_view(), name="login"),
    path('me/', ProfileView.as_view(), name="user_profile"),
    path('users/', UserModuleView.as_view(), name="all_users"),
    path('users/update/<str:user_id>', UserModuleView.as_view(), name="update_user"),
    path('users/<str:user_id>', UserModuleView.as_view(), name="delete_user"),
    path('permissions/update/', SetPermissionsView.as_view(), name="update_permissions"),
    path('permissions/<str:role>/', GetPermissionsView.as_view(), name="fetch_permissions"),
]
