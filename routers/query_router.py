import traceback
import json
import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from schemas.query_schema import QueryRequest, QueryResponse, QueryHistoryRequest, QueryHistoryResponse
from utils.logger import log_performance, logger
from utils.openai_funcs import get_openai_response
from utils.constants import QUERY_CLASSIFICATION_USER_PROMPT, QUERY_CLASSIFICATION_SYSTEM_PROMPT , \
GREET_USER_PROMPT, GREET_SYSTEM_PROMPT, RESPONSE_GENERATION_USER_PROMPT, RESPONSE_GENERATION_SYSTEM_PROMPT , \
COST_EFFECTIVE_ANALYSIS_SYSTEM_PROMPT , COST_EFFECTIVE_ANALYSIS_USER_PROMPT
from utils.pinecone_funcs import retrieve_chunks
from utils.helpers import retreive_articles
from utils.db_operations import insert_query_history, retrieve_query_history
router = APIRouter()


@log_performance
@router.post("/query", response_model=QueryResponse)
async def query_api(request: QueryRequest):
    """
    This API is used to handle the query from the user. 
    It classifies the query and generates a response based on the classification.
    It also inserts the query into the database. 

    Args:
        request: QueryRequest

    Returns:
        QueryResponse 
    """
    try:
        type = get_openai_response(
            messages=[
                {
                    "role": "system",
                    "content": QUERY_CLASSIFICATION_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": QUERY_CLASSIFICATION_USER_PROMPT.format(query=request.query)
                }
            ],
            is_json=True
        )
        type = json.loads(type)['type']

        if type == "garbage":
            response = "I guess you are typed some gibberish. Please type a valid query."

        elif type == "greet":
            request.messages.append(
                {
                    "role": "system",
                    "content": GREET_SYSTEM_PROMPT
                }
            )
            request.messages.append(
                {
                    "role": "user",
                    "content": GREET_USER_PROMPT.format(query=request.query)
                }
            )
            response = get_openai_response(
                messages=request.messages,
                is_json=False
            )
            
        elif type == "cost_effective_analysis":
            articles_context = retreive_articles(request.query)

            messages = []
            messages.append(
                {
                    "role": "system",
                    "content": COST_EFFECTIVE_ANALYSIS_SYSTEM_PROMPT,
                }
            )
            messages.append(
                                {
                    "role": "user",
                    "content": COST_EFFECTIVE_ANALYSIS_USER_PROMPT.format(
                        query=request.query,
                        articles_context=articles_context
                    )
                }
            )
            response = get_openai_response(
                messages=messages,
                is_json=True
            )
            response = json.loads(response)
            articles = response['articles']
            query_id = "query_"+str(uuid.uuid4())

            insert_query_history(
                request.user_id, 
                query_id, 
                request.query, 
                articles
            )

            
        else:
            chunks = retrieve_chunks(
                namespace="chatbot",
                query=request.query
            )

            context = '\n'.join(chunks) if chunks is not None else ""

            request.messages.append(
                {
                    "role": "system",
                    "content": RESPONSE_GENERATION_SYSTEM_PROMPT
                }
            )
            request.messages.append(
                {
                    "role": "user",
                    "content": RESPONSE_GENERATION_USER_PROMPT.format(
                        context=context,
                        query=request.query
                    )
                }
            )
            response = get_openai_response(
                messages=request.messages,
                is_json=False
            )

        return JSONResponse(content={"message": response , "is_graph": type == "cost_effective_analysis"})
    except Exception as e:
        logger.error(f"Error in query router: {traceback.format_exc()}")
        return JSONResponse(content={"message": f"Internal Server Error {e}"}, status_code=500)



@log_performance
@router.post("/query_history", response_model=QueryHistoryResponse)
async def query_history_api(request: QueryHistoryRequest):
    """
    This API is used to retrieve the query history from the database.

    Args:
        request: QueryHistoryRequest

    Returns:
        QueryHistoryResponse
    """
    try:
        query_history = retrieve_query_history(request.user_id)
        return JSONResponse(content={"message": query_history})
    except Exception as e:
        logger.error(f"Error in query history router: {traceback.format_exc()}")
        return JSONResponse(content={"message": f"Internal Server Error {e}"}, status_code=500)