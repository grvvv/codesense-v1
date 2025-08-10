from django.urls import path
from ..views.scan_views import ScanCreateView, ScanProgressView, ScanListView

urlpatterns = [
    path("create/", ScanCreateView.as_view(), name="create-scan"),
    path("<str:scan_id>/", ScanProgressView.as_view(), name="scan-detail"),
    path("project/<str:project_id>/", ScanListView.as_view(), name="scan-list"),
]
