import traceback

from fastapi import APIRouter, File, Form, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from schemas.user_schema import User, SaveArticles, GetArticlesAbstract, SendEmailRequest

from utils.db_operations import (
    create_user, 
    save_articles, 
    get_articles_abstract, 
    get_user_email,
    check_user_exists,
    check_email_exists
)
from utils.email_utils import send_email_with_pdf
from utils.pinecone_funcs import transfer_vectors_from_default_namespace
from utils.logger import logger

router = APIRouter()

def transfer_vectors_background(user_id: str):
    """
    Transfer vectors from default namespace to user's namespace in background
    
    Args:
        user_id (str): The user ID
    """
    try:
        result = transfer_vectors_from_default_namespace(user_id)
        if not result:
            logger.error(f"Failed to transfer vectors for user {user_id}")
    except Exception as e:
        logger.error(f"Error transferring vectors in background: {traceback.format_exc()}")

@router.post("/create_user")
async def create_user_api(request: User, background_tasks: BackgroundTasks):
    """
    Create a new user in the database

    Args:
        request: User - User object
        background_tasks: BackgroundTasks - FastAPI background tasks

    Returns:
        JSONResponse - JSON response
    """
    try:
        # Check if user already exists
        if check_user_exists(request.user_id):
            return JSONResponse(
                status_code=400,
                content={"message": "User ID already exists"}
            )
            
        # Check if email is already registered
        if check_email_exists(request.email):
            return JSONResponse(
                status_code=400,
                content={"message": "Email already registered"}
            )
            
        # Create user
        response = create_user(
            user_id=request.user_id,
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            created_at=request.created_at,
            last_sign_in_at=request.last_sign_in_at
        )
        
        if response:
            # Transfer vectors in background
            background_tasks.add_task(transfer_vectors_background, request.user_id)
            return JSONResponse(
                status_code=200,
                content={"message": "User created successfully"}
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"message": "Failed to create user"}
            )
            
    except Exception as e:
        logger.error(f"Error creating user: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"message": str(e)}
        )

@router.post("/save_articles")
async def save_articles_api(request: SaveArticles):
    """
    Save articles in the database
    """
    try:
        response = save_articles(
            user_id=request.user_id,
            article_ids=request.article_ids
        )
        if response:
            return JSONResponse(status_code=200, content={"message": "Articles saved successfully"})
        else:
            return JSONResponse(status_code=400, content={"message": "Articles saving failed"})
    except Exception as e:
        logger.error(f"Error saving articles: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"message": str(e)})

@router.post("/get_articles_abstract")
async def get_articles_abstract_api(request: GetArticlesAbstract):
    """
    Get saved articles from the database

    Args:
        request: GetArticlesAbstract - GetArticlesAbstract object

    Returns:
        JSONResponse - JSON response
    """
    try:
        response = get_articles_abstract(request.article_ids)  
        return JSONResponse(status_code=200, content={"data": response})
    except Exception as e:
        logger.error(f"Error getting saved articles: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"message": str(e)})

@router.post("/send_email")
async def send_email_api(
    pdf_file: UploadFile = File(...),
    user_id: str = Form(...),
    query: str = Form(...)
):
    """
    Send email with PDF attachment to user

    Args:
        pdf_file: UploadFile - PDF file
        user_id: str - User ID
        query: str - Query text

    Returns:
        JSONResponse - JSON response
    """
    try:
        # Get user's email from database
        user_email = get_user_email(user_id)
        if not user_email:
            return JSONResponse(status_code=404, content={"message": "User email not found"})

        # Send email with PDF
        await send_email_with_pdf(user_email, pdf_file, query)
        return JSONResponse(status_code=200, content={"success": True, "message": "Email sent successfully"})
    except Exception as e:
        logger.error(f"Error sending email: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})