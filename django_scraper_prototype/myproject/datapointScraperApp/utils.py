import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from .models import Datapoint, UserProfile
from django.contrib import messages

logger = logging.getLogger(__name__)

def perform_scraping(request, datapoints):
    """
    Performs scraping for a list of datapoints.
    """
    if not datapoints:
        messages.warning(request, "No Datapoints available for scraping.")
        return

    payload = {
        "tasks": []
    }

    for dp in datapoints:
        if not dp.url or not dp.xpath:
            logger.warning(f"Datapoint '{dp.name}' is missing 'url' or 'xpath'. Skipping.")
            messages.warning(request, f"Datapoint '{dp.name}' is missing 'url' or 'xpath'. Skipping.")
            continue

        if dp.data_type.upper() not in ['TXT', 'HTML']:
            logger.warning(f"Datapoint '{dp.name}' has invalid 'data_type': {dp.data_type}. Defaulting to 'TXT'.")
            data_type = 'TXT'
        else:
            data_type = dp.data_type.upper()

        payload["tasks"].append({
            "url": dp.url,
            "xpath": dp.xpath,
            "data_type": data_type
        })

    if not payload["tasks"]:
        messages.warning(request, "No valid Datapoints to scrape after validation.")
        return

    # Log the payload
    logger.debug(f"Scraping payload: {json.dumps(payload)}")

    # Retrieve the API token from Django settings
    API_TOKEN = settings.SCRAPER_API_TOKEN

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        # Send POST request to FastAPI scraper
        response = requests.post(
            "http://127.0.0.1:8001/scrape/batch",  # FastAPI batch endpoint on port 8001
            json=payload,
            headers=headers,
            timeout=60  # Adjust timeout as needed
        )

        logger.info(f"FastAPI Response Status Code: {response.status_code}")
        logger.info(f"FastAPI Response Content: {response.text}")

        if response.status_code == 200:
            response_data = response.json()
            results = response_data.get("results", [])

            for result in results:
                url = result.get("url")
                xpath = result.get("xpath")
                scraped_data = result.get("scraped_data")
                status = result.get("status")
                error = result.get("error")

                try:
                    # Retrieve the corresponding Datapoint instance
                    dp = Datapoint.objects.get(url=url, xpath=xpath)

                    if status == "success":
                        # Compare scraped_data with current_verified_data
                        if dp.current_verified_data == scraped_data:
                            dp.status = Datapoint.STATUS_AUTO
                            messages.success(request, f"No changes detected for Datapoint: {dp.name}. Status set to AUTO.")
                        else:
                            dp.status = Datapoint.STATUS_VERIFY
                            messages.info(request, f"Changes detected for Datapoint: {dp.name}. Status set to VERIFY for user verification.")

                        dp.current_unverified_data = scraped_data
                        dp.last_verified = timezone.now()
                        dp.last_updated = timezone.now()
                        dp.save()
                    else:
                        dp.status = Datapoint.STATUS_FIX
                        dp.last_updated = timezone.now()
                        dp.save()
                        messages.error(request, f"Failed to scrape Datapoint: {dp.name}. Error: {error}")
                except Datapoint.DoesNotExist:
                    messages.error(request, f"Datapoint with URL {url} and XPath {xpath} does not exist.")

        else:
            # Attempt to extract error message from FastAPI response
            try:
                error_detail = response.json().get("detail", "Unknown error")
            except json.JSONDecodeError:
                error_detail = response.text  # Capture raw response
            logger.error(f"FastAPI Error Response: {response.text}")
            messages.error(request, f"Failed to initiate scraping: {error_detail}")

    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException: {e}")
        messages.error(request, f"Error connecting to the scraper service: {e}")
    except json.JSONDecodeError:
        logger.error("JSONDecodeError: Invalid response from FastAPI.")
        messages.error(request, "Invalid response from the scraper service.")


def get_user_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user)
    if created:
        # Initialize with default preferences
        profile.column_preferences = {
            '0': True,
            '1': True,
            '2': True,
            '3': True,
            '4': True,
            '5': True,
            '6': True,
            '7': True,
            '8': True,
        }
        profile.theme = 'light'
        profile.save()
    return profile