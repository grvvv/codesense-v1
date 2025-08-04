# projects/urls.py
from django.urls import path
from ..views.finding_views import FindingDetailView, FindingListCreateView

urlpatterns = [
    path('scan/<str:scan_id>/', FindingListCreateView.as_view(), name="findings_by_scan"),
    path('<str:finding_id>/', FindingDetailView.as_view(), name="finding_by_id"),
]
