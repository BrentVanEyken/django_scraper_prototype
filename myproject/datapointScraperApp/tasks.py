from celery import shared_task
from django.utils import timezone
from .models import Datapoint, DataGroup, Organization
from .scraper.scraper import update_datapoint  # Your existing scraper function
import logging

logger = logging.getLogger(__name__)

@shared_task
def scrape_datapoint_task(datapoint_id):
    """
    Celery task to scrape data for a single Datapoint.
    
    Args:
        datapoint_id (int): The ID of the Datapoint to scrape.
    """
    try:
        datapoint = Datapoint.objects.get(id=datapoint_id)
        
        if datapoint.status != Datapoint.STATUS_AUTO:
            logger.debug(f"Datapoint '{datapoint.name}' (ID: {datapoint.id}) is not in 'AUTO' status. Skipping scraping.")
            return
        
        # Perform scraping and update the Datapoint
        update_datapoint(datapoint)
        
        logger.info(f"Successfully scraped and updated Datapoint '{datapoint.name}' (ID: {datapoint.id}).")
    except Datapoint.DoesNotExist:
        logger.error(f"Datapoint with ID {datapoint_id} does not exist.")
    except Exception as e:
        logger.error(f"Error scraping Datapoint ID {datapoint_id}: {e}")
        
        # Optionally, set status to 'FIX' to indicate an issue
        try:
            datapoint.status = Datapoint.STATUS_FIX
            datapoint.save(update_fields=['status'])
            logger.debug(f"Set status to 'FIX' for Datapoint '{datapoint.name}' (ID: {datapoint.id}).")
        except Exception as inner_e:
            logger.error(f"Failed to update status for Datapoint ID {datapoint_id}: {inner_e}")

@shared_task
def scrape_datagroup_task(datagroup_id):
    """
    Celery task to scrape all Datapoints within a DataGroup.
    
    Args:
        datagroup_id (int): The ID of the DataGroup to scrape.
    """
    try:
        datagroup = DataGroup.objects.get(id=datagroup_id)
        datapoints = datagroup.datapoints.all()
        
        if not datapoints.exists():
            logger.warning(f"No Datapoints found in DataGroup '{datagroup.name}' (ID: {datagroup.id}).")
            return
        
        for datapoint in datapoints:
            if datapoint.status == Datapoint.STATUS_AUTO:
                scrape_datapoint_task.delay(datapoint.id)
        
        logger.info(f"Enqueued scraping tasks for DataGroup '{datagroup.name}' (ID: {datagroup.id}).")
    except DataGroup.DoesNotExist:
        logger.error(f"DataGroup with ID {datagroup_id} does not exist.")
    except Exception as e:
        logger.error(f"Error scraping DataGroup ID {datagroup_id}: {e}")

@shared_task
def scrape_organisation_task(organisation_id):
    """
    Celery task to scrape all Datapoints/Datagroups associated with an Organization.
    
    Args:
        organisation_id (int): The ID of the Organization to scrape.
    """
    try:
        organisation = Organization.objects.get(id=organisation_id)
        # Assuming Organization has related DataGroups and/or directly related Datapoints
        # Adjust the following based on your actual model relationships
        
        # Scrape all Datapoints directly associated with the Organization
        direct_datapoints = organisation.datapoints.all()
        for datapoint in direct_datapoints:
            if datapoint.status == Datapoint.STATUS_AUTO:
                scrape_datapoint_task.delay(datapoint.id)
        
        # Scrape all Datapoints within DataGroups associated with the Organization
        datagroups = organisation.datagroups.all()  # Assuming a related_name 'datagroups' in Organization model
        for datagroup in datagroups:
            scrape_datagroup_task.delay(datagroup.id)
        
        logger.info(f"Enqueued scraping tasks for Organization '{organisation.name}' (ID: {organisation.id}).")
    except Organization.DoesNotExist:
        logger.error(f"Organization with ID {organisation_id} does not exist.")
    except Exception as e:
        logger.error(f"Error scraping Organization ID {organisation_id}: {e}")

@shared_task
def scrape_all_datapoints_task():
    """
    Celery task to scrape all Datapoints in the system.
    """
    try:
        datapoints = Datapoint.objects.filter(status=Datapoint.STATUS_AUTO)
        
        if not datapoints.exists():
            logger.warning("No Datapoints with status 'AUTO' found to scrape.")
            return
        
        for datapoint in datapoints:
            scrape_datapoint_task.delay(datapoint.id)
        
        logger.info("Enqueued scraping tasks for all Datapoints with status 'AUTO'.")
    except Exception as e:
        logger.error(f"Error scraping all Datapoints: {e}")
