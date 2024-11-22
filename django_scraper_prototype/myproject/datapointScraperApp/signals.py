from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
from .models import Datapoint
import logging

logger = logging.getLogger(__name__)

# @receiver(post_save, sender=Datapoint)
# def trigger_scraping_on_auto_status(sender, instance, created, **kwargs):
#     """
#     Signal handler to trigger scraping when a Datapoint with status 'AUTO' is created.
#     """
#     if created and instance.status == Datapoint.STATUS_AUTO:
#         logger.debug(f"Enqueuing scraping task for Datapoint '{instance.name}' (ID: {instance.id}).")
#         scrape_datapoint_task.delay(instance.id)

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()