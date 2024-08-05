from django.urls import path

from ap.database_access import views

app_name = "database_access"

urlpatterns = [
    path("", views.DatabaseListView.as_view(), name="list"),
]
