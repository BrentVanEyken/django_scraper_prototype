
from celery import shared_task
from django.core.management import call_command

@shared_task
def run_scraper_task():
    """
    Celery task to run the scraper management command.
    """
    call_command('run_scraper')