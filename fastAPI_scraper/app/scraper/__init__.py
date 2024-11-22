from typing import Optional
from lxml import html
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def get_page(url: str, wait_xpath: Optional[str] = None) -> html.HtmlElement:
    """
    Fetches the page content using Playwright, waiting for a specific element if provided.

    Args:
        url (str): The URL of the website to fetch.
        wait_xpath (Optional[str]): The XPath of the element to wait for.

    Returns:
        html.HtmlElement: The parsed HTML tree of the page content.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, timeout=13000)

            if wait_xpath:
                # Wait for the element matching the XPath to be visible
                page.wait_for_selector(f'xpath={wait_xpath}', timeout=13000)
            else:
                # Wait for the network to be idle
                page.wait_for_load_state('networkidle', timeout=13000)

            content = page.content()
            tree = html.fromstring(content)
            browser.close()
            return tree
    except PlaywrightTimeoutError:
        raise RuntimeError("Timeout while waiting for the element to appear.")
    except Exception as e:
        raise RuntimeError(f"Error fetching the page: {e}")

def scrape_content_txt(url: str, xpath: str) -> Optional[str]:
    """
    Scrape text content from the given URL using the provided XPath,
    combining the text of multiple elements into a single string.

    Args:
        url (str): The URL of the website to scrape.
        xpath (str): The XPath to target the content.

    Returns:
        Optional[str]: Combined text content from all matching elements, or None if no content found.
    """
    try:
        tree = get_page(url)
        result = tree.xpath(xpath)

        if result:
            # Combine all matching elements' text content into a single string
            combined_text = " ".join([
                element.text_content().strip() for element in result if element.text_content()
            ])
            return combined_text if combined_text else None
        else:
            return None
    except Exception as e:
        raise RuntimeError(f"Error during scraping: {e}")

def scrape_content_html(url: str, xpath: str) -> Optional[str]:
    """
    Scrape HTML content from the given URL using the provided XPath,
    combining the HTML of multiple elements into a single string.

    Args:
        url (str): The URL of the website to scrape.
        xpath (str): The XPath to target the content.

    Returns:
        Optional[str]: Combined HTML from all matching elements, or None if no content found.
    """
    try:
        tree = get_page(url)
        result = tree.xpath(xpath)

        if result:
            # Combine all matching elements' HTML content into a single string
            combined_html = " ".join([
                html.tostring(element, pretty_print=True, encoding="unicode") for element in result
            ])
            return combined_html if combined_html else None
        else:
            return None
    except Exception as e:
        raise RuntimeError(f"Error during scraping: {e}")
