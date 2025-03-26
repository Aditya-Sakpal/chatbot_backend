import traceback
from urllib.parse import urlparse, urljoin
import uuid
from typing import List, Set
import asyncio

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from utils.logger import logger
from utils.data_upload_utils import get_chunks
from utils.openai_funcs import get_embeddings
from utils.pinecone_funcs import upsert_chunks
from utils.db_operations import update_web_crawl_urls, update_job_status

def get_domain(url: str) -> str:
    """
    Get the domain from a url

    Args:
        url: str - The url to get the domain from

    Returns:
        str - The domain of the url
    """
    parsed_uri = urlparse(url)
    return '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

def setup_selenium_driver():
    """
    Setup Chrome driver with headless options

    Returns:
        webdriver.Chrome - The Chrome driver
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)

def get_page_content(driver: webdriver.Chrome, url: str) -> str:
    """
    Get page content using Selenium

    Args:
        driver: webdriver.Chrome - The Chrome driver
        url: str - The url to get the content from 

    Returns:
        str - The content of the page
    """
    try:
        driver.get(url)
        # Wait for body to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return driver.page_source
    except Exception as e:
        logger.error(f"Error getting content for {url}: {str(e)}")
        return ""

def extract_links(html: str, domain: str) -> Set[str]:
    """
    Extract links from HTML that belong to the same domain

    Args:
        html: str - The HTML content of the page
        domain: str - The domain of the url

    Returns:
        Set[str] - The links of the page
    """
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(domain, href)
        
        # Only include links from the same domain
        if full_url.startswith(domain):
            links.add(full_url)
    
    return links

async def process_and_upsert_content(content: str, user_id: str) -> bool:
    """
    Process page content and upsert to Pinecone

    Args:
        content: str - The content of the page
        user_id: str - The user id

    Returns:
        bool - True if the content was upserted, False otherwise
    """
    try:
        # Get chunks from content
        chunks = get_chunks(content)
        
        # Prepare vectors
        vectors = []
        for chunk in chunks:
            vector = get_embeddings(chunk)
            vectors.append({
                "id": str(uuid.uuid4()),
                "values": vector,
                "metadata": {
                    "text": chunk
                }
            })
        
        # Upsert chunks
        return upsert_chunks(vectors, user_id)
    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        return False

async def crawl_website(url: str, user_id: str, job_id: str, depth: int = 1):
    """
    Crawl website and process content in background

    Args:
        url: str - The url to crawl
        user_id: str - The user id
        job_id: str - The job id for status tracking
        depth: int - Maximum number of pages to crawl (default: 1)
    """
    try:
        update_job_status(job_id, "pending")
        # Add URL to web_crawl_urls array
        update_web_crawl_urls(user_id, url)
        
        domain = get_domain(url)
        driver = setup_selenium_driver()
        visited_urls = set()
        urls_to_visit = {url}

        try:
            while urls_to_visit and len(visited_urls) < depth:
                current_url = urls_to_visit.pop()
                
                if current_url in visited_urls:
                    continue
                
                logger.info(f"Crawling: {current_url}")
                content = get_page_content(driver, current_url)
                
                if content:
                    # Process and upsert content
                    success = await process_and_upsert_content(content, user_id)
                    if success:
                        visited_urls.add(current_url)
                        
                        # Extract new links
                        new_links = extract_links(content, domain)
                        urls_to_visit.update(new_links - visited_urls)
                
                # Small delay to be respectful to the server
                await asyncio.sleep(1)
                
            # Update job status to succeeded
            update_job_status(job_id, "succeeded")
                
        except Exception as e:
            # Update job status to failed with error message
            update_job_status(job_id, "failed", str(e))
            raise e
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Error in crawl_website: {traceback.format_exc()}")
        # Update job status to failed with error message
        update_job_status(job_id, "failed", str(e))
        raise e 