from django.urls import path

from . import views

app_name = "databases"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="index"),
    path("projects/create/", views.ProjectCreateView.as_view(), name="project-create"),
    path("projects/<slug:slug>/", views.ProjectDetailView.as_view(), name="project-detail"),
]
