from django.apps import AppConfig
class DatapointScraperAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'datapointScraperApp'

    def ready(self):
        import datapointScraperApp.signals  # Ensure signal handlers are connecte
