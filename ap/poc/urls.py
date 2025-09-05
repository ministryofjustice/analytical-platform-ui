from django.urls import path

from . import views

app_name = "poc"

urlpatterns = [
    path("", views.SharedResourceListView.as_view(), name="index"),
    # path("<int:pk>/resources/", views.RAMShareResourcesView.as_view(), name="resources"),
    path("refresh/", views.RefreshSharedResourceView.as_view(), name="refresh_shared_resources"),
    path("delete/", views.DeleteSharedResourceView.as_view(), name="delete_shared_resources"),
]
