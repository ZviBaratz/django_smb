from django.urls import path
from django_smb import views

urlpatterns = [
    path(
        'remote_locations/',
        views.RemoteLocationListView.as_view(),
        name='smb_locations',
    ),
    path(
        'create_remote_location/',
        views.RemoteLocationCreateView.as_view(),
        name='smb_create',
    ),
    path(
        'sync/<int:pk>/',
        views.sync_remote_location,
        name='smb_sync',
    ),
]
