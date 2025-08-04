from django.urls import path, include

urlpatterns = [
    path('projects/', include('local.api_app.urls.project_urls')),
    # path('scans/', include('local.api_app.urls.scan_urls')),
    path('findings/', include('local.api_app.urls.finding_urls')),
]
