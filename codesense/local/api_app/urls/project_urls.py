# projects/urls.py
from django.urls import path
from ..views.project_views import ProjectListCreateView, ProjectDetailView

urlpatterns = [
    path('', ProjectListCreateView.as_view()),
    path('<str:project_id>/', ProjectDetailView.as_view()),
]
