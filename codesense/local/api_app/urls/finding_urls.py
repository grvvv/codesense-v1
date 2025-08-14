# projects/urls.py
from django.urls import path
from ..views.finding_views import FindingDetailView, FindingListCreateView, ExportFindingView

urlpatterns = [
    path('scan/csv/<str:scan_id>/', ExportFindingView.as_view(), name="export_findings_by_scan"),
    path('scan/<str:scan_id>/', FindingListCreateView.as_view(), name="findings_by_scan"),
    path('approve/<str:finding_id>/', FindingDetailView.as_view(), name="approve_finding"),
    path('delete/<str:finding_id>/', FindingDetailView.as_view(), name="delete_finding"),
    path('<str:finding_id>/', FindingDetailView.as_view(), name="finding_by_id"),
]
