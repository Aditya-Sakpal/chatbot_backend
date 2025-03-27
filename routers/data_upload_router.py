import traceback
import requests
import uuid
import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import  List

from utils.logger import logger
from schemas.data_upload_schema import ScrapeSingleUrlRequest, ScrapeSingleUrlResponse, WebCrawlRequest, WebCrawlResponse, \
    WebCrawlStatusRequest, WebCrawlStatusResponse, FetchSinglePageUrlsRequest, FetchSinglePageUrlsResponse, \
    FetchWebCrawlUrlsRequest, FetchWebCrawlUrlsResponse, FetchDocumentsRequest, FetchDocumentsResponse

from utils.data_upload_utils import get_chunks
from utils.openai_funcs import get_embeddings
from utils.pinecone_funcs import upsert_chunks
from utils.db_operations import (
    update_single_page_urls,
    create_crawling_job,
    get_job_status,
    update_user_documents,
    get_user_documents,
    get_single_page_urls,
    get_web_crawl_urls
)
from utils.document_processor import process_and_upsert_documents
from utils.web_crawler import crawl_website

router = APIRouter()

def process_url_content_background(url: str, content: str, user_id: str):
    """
    Process URL content and upsert chunks in background
    
    Args:
        url (str): The URL being processed
        content (str): The HTML content of the URL
        user_id (str): The user ID
    """
    try:
        chunks = get_chunks(content)
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
        result = upsert_chunks(vectors, user_id)

        if not result:
            logger.error(f"Failed to upsert chunks for URL: {url}")
    except Exception as e:
        logger.error(f"Error processing URL content in background: {traceback.format_exc()}")

@router.post('/scrape_single_url', response_model=ScrapeSingleUrlResponse)
async def scrape_single_url_api(
    request: ScrapeSingleUrlRequest,
    background_tasks: BackgroundTasks
):
    """
    Scrape a single url and upsert the chunks into Pinecone

    Args:
        request: ScrapeSingleUrlRequest - The request object
        background_tasks: BackgroundTasks - FastAPI background tasks
    
    Returns:
        ScrapeSingleUrlResponse - The response object with the scraped url text
    """
    try:
        response = requests.get(request.url)
        if response.status_code != 200:
            raise Exception(f"Failed to scrape url: {request.url}")
        
        # Update single page URLs immediately
        update_single_page_urls(request.user_id, request.url)
        
        # Process content and upsert chunks in background
        background_tasks.add_task(
            process_url_content_background,
            request.url,
            response.text,
            request.user_id
        )

        return JSONResponse(
            status_code=200,
            content={"message": "URL scraping started successfully. Processing will continue in the background."}
        )
    except Exception as e:
        logger.error(f"Error scraping single url: {traceback.format_exc()}")
        raise e

def start_crawling(url: str, user_id: str):
    """
    Start crawling a single url

    Args:
        url: str - The url to crawl
        user_id: str - The user id

    Returns:
        None    
    """
    asyncio.run(crawl_website(url, user_id))

@router.post('/web_crawl', response_model=WebCrawlResponse)
async def web_crawl_api(request: WebCrawlRequest, background_tasks: BackgroundTasks):
    """
    Web crawl a single url and upsert the chunks into Pinecone

    Args:
        request: WebCrawlRequest - The request object containing URL, user_id, and depth
        background_tasks: BackgroundTasks - FastAPI background tasks

    Returns:
        WebCrawlResponse - Job information including job_id and status
    """
    try:
        # Create a new crawling job
        job_id = create_crawling_job(request.user_id, request.url)
        
        # Start crawling in background with specified depth
        background_tasks.add_task(
            crawl_website,
            request.url,
            request.user_id,
            job_id,
            request.depth
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "job_id": job_id,
                "status": "pending",
                "url": request.url,
                "depth": request.depth,
                "message": f"Web crawling started successfully. Will crawl up to {request.depth} pages."
            }
        )
    except Exception as e:
        logger.error(f"Error starting web crawl: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error starting web crawl: {str(e)}"}
        )

@router.post("/web_crawl/{job_id}", response_model=WebCrawlStatusResponse)
async def get_web_crawl_status(
    request: WebCrawlStatusRequest
):
    """
    Get the status of a web crawling job
    
    Args:
        job_id: str - The ID of the crawling job
        user_id: str - The user ID from the current user
        
    Returns:
        dict: Job status information
    """
    try:
        job_status = get_job_status(request.job_id, request.user_id)
        if not job_status:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        return JSONResponse(
            status_code=200,
            content={
                "job_id": request.job_id,
                "status": job_status['status']
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting job status: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )

@router.post("/fetch_single_page_urls", response_model=FetchSinglePageUrlsResponse)
async def get_user_single_page_urls(request: FetchSinglePageUrlsRequest ):
    """
    Get all single page URLs for a user
    
    Args:
        user_id: str - The user ID
        
    Returns:
        dict: List of single page URLs
    """
    try:
        urls = get_single_page_urls(request.user_id)
        return JSONResponse(
            status_code=200,
            content={
                "user_id": request.user_id,
                "urls": urls
            }
        )
    except Exception as e:
        logger.error(f"Error getting single page URLs: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get single page URLs: {str(e)}"
        )

@router.post("/fetch_web_crawl_urls", response_model=FetchWebCrawlUrlsResponse)
async def get_user_web_crawl_urls(request: FetchWebCrawlUrlsRequest):
    """
    Get all web crawl URLs for a user
    
    Args:
        user_id: str - The user ID
        
    Returns:
        dict: List of web crawl URLs
    """
    try:
        urls = get_web_crawl_urls(request.user_id)
        return JSONResponse(
            status_code=200,
            content={
                "user_id": request.user_id,
                "urls": urls
            }
        )
    except Exception as e:
        logger.error(f"Error getting web crawl URLs: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get web crawl URLs: {str(e)}"
        )

@router.post("/upload_documents")
async def upload_documents(
    files: List[UploadFile] = File(...),
    user_id: str = Form(...)
):
    """
    Upload and process multiple documents
    
    Args:
        files: List[UploadFile] - List of uploaded files
        user_id: str - User ID
        
    Returns:
        JSONResponse - Success/failure message
    """
    try:
        # Process documents and get list of successfully processed files
        processed_docs = await process_and_upsert_documents(files, user_id)
        
        if processed_docs:
            # Update user's documents array
            update_user_documents(user_id, processed_docs)
            
            return JSONResponse(
                status_code=200,
                content={
                    "message": f"Successfully processed {len(processed_docs)} documents",
                    "documents": processed_docs
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"message": "No documents were successfully processed"}
            )
            
    except Exception as e:
        logger.error(f"Error uploading documents: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error uploading documents: {str(e)}"}
        )

@router.post("/fetch_documents", response_model=FetchDocumentsResponse)
async def fetch_documents(request: FetchDocumentsRequest):
    """
    Fetch all documents for a user
    
    Args:
        request: FetchDocumentsRequest - Request containing user_id
        
    Returns:
        FetchDocumentsResponse - List of document names
    """
    try:
        documents = get_user_documents(request.user_id)
        return JSONResponse(
            status_code=200,
            content={"documents": documents}
        )
    except Exception as e:
        logger.error(f"Error fetching documents: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch documents: {str(e)}"
        )
