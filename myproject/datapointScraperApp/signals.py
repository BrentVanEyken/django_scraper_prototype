from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Datapoint
from .tasks import scrape_datapoint_task
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Datapoint)
def trigger_scraping_on_auto_status(sender, instance, created, **kwargs):
    """
    Signal handler to trigger scraping when a Datapoint with status 'AUTO' is created.
    """
    if created and instance.status == Datapoint.STATUS_AUTO:
        logger.debug(f"Enqueuing scraping task for Datapoint '{instance.name}' (ID: {instance.id}).")
        scrape_datapoint_task.delay(instance.id)