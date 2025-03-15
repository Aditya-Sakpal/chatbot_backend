import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from schemas.user_schema import User

from utils.db_operations import create_user
from utils.logger import logger

router = APIRouter()

@router.post("/create_user")
async def create_user_api(request: User):
    """
    Create a new user in the database

    Args:
        request: User - User object

    Returns:
        JSONResponse - JSON response
    """
    try:
        response  = create_user(
            user_id=request.user_id,
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            created_at=request.created_at,
            last_sign_in_at=request.last_sign_in_at
        )
        if response:
            return JSONResponse(status_code=200, content={"message": "User created successfully"})
        else:
            return JSONResponse(status_code=400, content={"message": "User creation failed"})
    except Exception as e:
        logger.error(f"Error creating user: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"message": str(e)})    
