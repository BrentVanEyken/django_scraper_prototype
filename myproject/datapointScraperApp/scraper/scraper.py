# datapointScraperApp/scraper/scraper.py

from datetime import timezone
from typing import Optional
from lxml import html
from datapointScraperApp.models import Datapoint
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging

# Configure logger
logger = logging.getLogger(__name__)

def get_page(url: str, wait_xpath: Optional[str] = None) -> html.HtmlElement:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, timeout=10000)

            if wait_xpath:
                page.wait_for_selector(f'xpath={wait_xpath}', timeout=5000)
            else:
                page.wait_for_load_state('networkidle', timeout=5000)

            content = page.content()
            tree = html.fromstring(content)
            browser.close()
            return tree
    except PlaywrightTimeoutError:
        logger.error(f"Timeout while waiting for the element: {wait_xpath} on URL: {url}")
        raise RuntimeError("Timeout while waiting for the element to appear.")
    except Exception as e:
        logger.error(f"Error fetching the page: {url} - {e}")
        raise RuntimeError(f"Error fetching the page: {e}")

def scrape_content_txt(url: str, xpath: str) -> Optional[str]:
    try:
        tree = get_page(url)
        result = tree.xpath(xpath)

        if result:
            combined_text = " ".join([
                element.text_content().strip() for element in result if element.text_content()
            ])
            return combined_text if combined_text else None
        else:
            logger.warning(f"No content found for XPath: {xpath} on URL: {url}")
            return None
    except Exception as e:
        logger.error(f"Error during scraping text from URL: {url} - {e}")
        raise RuntimeError(f"Error during scraping: {e}")

def scrape_content_html(url: str, xpath: str) -> Optional[str]:
    try:
        tree = get_page(url)
        result = tree.xpath(xpath)

        if result:
            combined_html = " ".join([
                html.tostring(element, pretty_print=True, encoding="unicode") for element in result
            ])
            return combined_html if combined_html else None
        else:
            logger.warning(f"No content found for XPath: {xpath} on URL: {url}")
            return None
    except Exception as e:
        logger.error(f"Error during scraping HTML from URL: {url} - {e}")
        raise RuntimeError(f"Error during scraping: {e}")

def update_datapoint(datapoint: Datapoint):
    """
    Scrapes data based on the Datapoint's data_type and updates fields accordingly.
    """
    try:
        if datapoint.data_type.upper() == 'HTML':
            scraped_data = scrape_content_html(datapoint.url, datapoint.xpath)
        else:
            scraped_data = scrape_content_txt(datapoint.url, datapoint.xpath)

        if scraped_data:
            datapoint.current_unverified_data = scraped_data
            datapoint.last_updated = timezone.now()

            if datapoint.status == Datapoint.STATUS_AUTO:
                datapoint.status = Datapoint.STATUS_VERIFY

            datapoint.save()
            logger.info(f"Updated Datapoint ID: {datapoint.id} with new data.")
        else:
            logger.warning(f"No data scraped for Datapoint ID: {datapoint.id}.")
            # Optionally, set status to 'FIX' if scraping fails silently
            if datapoint.status == Datapoint.STATUS_AUTO:
                datapoint.status = Datapoint.STATUS_FIX
                datapoint.save(update_fields=['status'])
                logger.debug(f"Set status to 'FIX' for Datapoint ID: {datapoint.id} due to no data.")
    except Exception as e:
        logger.error(f"Error updating Datapoint ID: {datapoint.id} - {e}")
        # Optionally, set status to 'FIX' to indicate an issue
        if datapoint.status == Datapoint.STATUS_AUTO:
            datapoint.status = Datapoint.STATUS_FIX
            datapoint.save(update_fields=['status'])
            logger.debug(f"Set status to 'FIX' for Datapoint ID: {datapoint.id} due to exception.")
        raise
