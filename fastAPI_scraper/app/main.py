import sys
import asyncio
import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
import json
import logging
from dotenv import load_dotenv
from pathlib import Path  # For path management

from . import scraper as s  # Ensure scraper.py is in the same directory

# Set event loop policy for Windows if necessary
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

API_TOKEN = os.getenv("SCRAPER_API_TOKEN")

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="FastAPI Web Scraper")

# Pydantic models for batch scraping
class ScrapeTask(BaseModel):
    url: str
    xpath: str
    data_type: Optional[str] = "TXT"  # Default to TXT; can be "HTML" if needed

class ScrapeBatchRequest(BaseModel):
    tasks: List[ScrapeTask]

@app.get("/debug/token")
def debug_token():
    """
    Debugging endpoint to verify API_TOKEN loading.
    **Do not use in production!**
    """
    return {"API_TOKEN": API_TOKEN}

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI web scraper!"}

@app.get("/scrape/txt")
def scrape_content_txt(url: str, xpath: str):
    """
    Scrape text content from a website using the provided URL and XPath.
    """
    try:
        # Call the scraper function to get the content
        scraped_data = s.scrape_content_txt(url, xpath)
        if scraped_data:
            return {"scraped_data": scraped_data}
        else:
            return {"error": "No content found at the provided XPath."}
    except Exception as e:
        logger.error(f"Error in /scrape/txt: {e}")
        return {"error": f"An error occurred: {str(e)}"}

@app.get("/scrape/html")
def scrape_content_html(url: str, xpath: str):
    """
    Scrape HTML content from a website using the provided URL and XPath.
    """
    try:
        # Call the scraper function to get the content
        scraped_data = s.scrape_content_html(url, xpath)
        if scraped_data:
            return {"scraped_data": scraped_data}
        else:
            return {"error": "No content found at the provided XPath."}
    except Exception as e:
        logger.error(f"Error in /scrape/html: {e}")
        return {"error": f"An error occurred: {str(e)}"}

@app.post("/scrape/batch")
def scrape_batch(request: ScrapeBatchRequest, authorization: Optional[str] = Header(None)):
    """
    Batch scrape multiple Datapoints based on provided tasks.
    Expects a list of tasks each containing 'url', 'xpath', and optionally 'data_type'.
    """
    # Log the incoming authorization header
    logger.info(f"Authorization header received: {authorization}")
    logger.info(f"Expected API_TOKEN: {API_TOKEN}")

    # Authenticate the request
    if not authorization:
        logger.warning("Authorization header missing.")
        raise HTTPException(status_code=403, detail="Authorization header missing.")

    if authorization != f"Bearer {API_TOKEN}":
        logger.warning("Unauthorized access attempt.")
        raise HTTPException(status_code=403, detail="Unauthorized.")

    logger.info(f"Received batch scraping request: {request.tasks}")

    results = []

    for task in request.tasks:
        url = task.url
        xpath = task.xpath
        data_type = task.data_type.upper()

        try:
            if data_type == "TXT":
                scraped_data = s.scrape_content_txt(url, xpath)
            elif data_type == "HTML":
                scraped_data = s.scrape_content_html(url, xpath)
            else:
                raise ValueError(f"Unsupported data_type '{task.data_type}'. Use 'TXT' or 'HTML'.")

            if scraped_data:
                results.append({
                    "url": url,
                    "xpath": xpath,
                    "scraped_data": scraped_data,
                    "status": "success"
                })
                logger.info(f"Successfully scraped data for URL: {url}, XPath: {xpath}")
            else:
                results.append({
                    "url": url,
                    "xpath": xpath,
                    "error": "No content found at the provided XPath.",
                    "status": "failed"
                })
                logger.warning(f"No content found for URL: {url}, XPath: {xpath}")
        except Exception as e:
            results.append({
                "url": url,
                "xpath": xpath,
                "error": str(e),
                "status": "failed"
            })
            logger.error(f"Error scraping URL: {url}, XPath: {xpath}. Error: {e}")

    return {"results": results}
