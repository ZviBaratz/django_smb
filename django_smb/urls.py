from django.urls import path
from django_smb import views

app_name = 'django_smb'

urlpatterns = [
    path(
        'remote_locations/',
        views.RemoteLocationListView.as_view(),
        name='locations',
    ),
    path(
        'create_remote_location/',
        views.RemoteLocationCreateView.as_view(),
        name='create',
    ),
    path(
        'sync/<int:pk>/',
        views.sync_remote_location,
        name='sync',
    ),
    path(
        'jsonify/lazy/',
        views.generate_lazy_json,
        name='lazy_json',
    ),
    path(
        'jsonify/<int:pk>/',
        views.generate_json,
        name='jsonify',
    ),
]
