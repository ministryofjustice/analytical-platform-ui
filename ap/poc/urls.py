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
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/grant_permissions/",
        views.GrantDatabasePermissionsView.as_view(),
        name="grant_database_permissions",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/revoke_permissions/",
        views.RevokeDatabasePermissionsView.as_view(),
        name="revoke_database_permissions",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/",
        views.TableDetailView.as_view(),
        name="table_detail",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/grant_permissions/",
        views.GrantTablePermissionsView.as_view(),
        name="grant_table_permissions",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/revoke_permissions/",
        views.RevokeTablePermissionsView.as_view(),
        name="revoke_table_permissions",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/create_data_filter/",
        views.CreateDataFilterView.as_view(),
        name="create_data_filter",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/<str:filter_name>/update_data_filter/",
        views.UpdateDataFilterView.as_view(),
        name="update_data_filter",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/<str:filter_name>/",
        views.DataFilterDetailView.as_view(),
        name="data_filter_detail",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/<str:filter_name>/delete/",
        views.DeleteDataFilterView.as_view(),
        name="delete_data_filter",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/<str:filter_name>/grant_permissions/",
        views.GrantFilterPermissionsView.as_view(),
        name="grant_filter_permissions",
    ),
    path(
        "databases/<int:resource_catalog_id>/<str:database_rl_name>/<str:table_name>/<str:filter_name>/revoke_permissions/",
        views.RevokeFilterPermissionsView.as_view(),
        name="revoke_filter_permissions",
    ),
]
