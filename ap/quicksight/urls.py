from django.urls import path

from ap.quicksight.views import views

urlpatterns = [
    path("", views.QuicksightView.as_view(), name="index"),
]
