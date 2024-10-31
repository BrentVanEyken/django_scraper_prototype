# datapointScraperApp/management/commands/run_scraper.py

from django.core.management.base import BaseCommand
from datapointScraperApp.models import Datapoint
from datapointScraperApp.scraper.scraper import update_datapoint

class Command(BaseCommand):
    help = 'Runs the scraper to update Datapoint instances.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting scraper...'))

        # Fetch all Datapoints with status 'AUTO'
        datapoints = Datapoint.objects.filter(status='AUTO')

        if not datapoints.exists():
            self.stdout.write(self.style.WARNING('No Datapoints with status AUTO found.'))
            return

        for datapoint in datapoints:
            self.stdout.write(f"Updating Datapoint: {datapoint.name} (ID: {datapoint.id})")
            try:
                update_datapoint(datapoint)
                self.stdout.write(self.style.SUCCESS(f"Successfully updated Datapoint ID: {datapoint.id}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating Datapoint ID: {datapoint.id} - {e}"))

        self.stdout.write(self.style.SUCCESS('Scraper finished successfully.'))
