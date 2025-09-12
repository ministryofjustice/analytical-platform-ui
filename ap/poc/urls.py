from django.urls import path

from . import views

app_name = "poc"

urlpatterns = [
    path("", views.SharedResourceListView.as_view(), name="index"),
    # path("<int:pk>/resources/", views.RAMShareResourcesView.as_view(), name="resources"),
    path("refresh/", views.RefreshSharedResourceView.as_view(), name="refresh_shared_resources"),
    path("delete/", views.DeleteSharedResourceView.as_view(), name="delete_shared_resources"),
    path("databases/", views.DatabaseListView.as_view(), name="databases"),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/",
        views.DatabaseDetailView.as_view(),
        name="database_detail",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/grant_database_permissions/",
        views.GrantDatabasePermissionsView.as_view(),
        name="grant_database_permissions",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/revoke_database_permissions/",
        views.RevokeDatabasePermissionsView.as_view(),
        name="revoke_database_permissions",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/",
        views.TableDetailView.as_view(),
        name="table_detail",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/grant_table_permissions/",
        views.GrantTablePermissionsView.as_view(),
        name="grant_table_permissions",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/revoke_table_permissions/",
        views.RevokeTablePermissionsView.as_view(),
        name="revoke_table_permissions",
    ),
]
