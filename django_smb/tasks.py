from celery import shared_task
from django_smb.models import RemoteLocation


@shared_task
def sync_location(location_id: int) -> bool:
    location = RemoteLocation.objects.get(id=location_id)
    result = location.sync()
    return result