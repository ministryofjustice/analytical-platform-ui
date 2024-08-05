from django.urls import path

from ap.quicksight.views import views

app_name = "quicksight"

urlpatterns = [
    path("", views.QuicksightView.as_view(), name="index"),
]
