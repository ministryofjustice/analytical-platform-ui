from django.urls import path

from . import views

app_name = "poc"

urlpatterns = [
    path("", views.RAMShareView.as_view(), name="index"),
    path("<int:pk>/resources/", views.RAMShareResourcesView.as_view(), name="resources"),
    path("refresh/", views.RefreshRAMSharesView.as_view(), name="refresh_ram_shares"),
]
