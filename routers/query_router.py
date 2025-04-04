import traceback
import json
import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from schemas.query_schema import QueryRequest, QueryResponse, QueryHistoryRequest, QueryHistoryResponse, BubbleGraphDetailsRequest,\
BubbleGraphDetailsResponse, DescriptiveAnalysisRequest, DescriptiveAnalysisResponse, SaveSettingsRequest, SaveSettingsResponse, GetSettingsRequest, GetSettingsResponse ,\
GetLatestRelevantPublicationsRequest, GetLatestRelevantPublicationsResponse
from utils.logger import log_performance, logger
from utils.openai_funcs import get_openai_response
from utils.constants import QUERY_CLASSIFICATION_USER_PROMPT, QUERY_CLASSIFICATION_SYSTEM_PROMPT , \
GREET_USER_PROMPT, GREET_SYSTEM_PROMPT, RESPONSE_GENERATION_USER_PROMPT, RESPONSE_GENERATION_SYSTEM_PROMPT , \
COST_EFFECTIVE_ANALYSIS_SYSTEM_PROMPT , COST_EFFECTIVE_ANALYSIS_USER_PROMPT
from utils.pinecone_funcs import retrieve_chunks
from utils.helpers import retreive_articles, retreive_modality_count
from utils.db_operations import insert_query_history, retrieve_query_history, retrieve_descriptive_analysis, save_chatbot_settings , get_chatbot_settings ,\
      get_saved_articles_ids , get_articles_from_query_history 

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
        # Get user's settings
        settings = request.settings
        
        type = get_openai_response(
            messages=[
                {
                    "role": "system",
                    "content": QUERY_CLASSIFICATION_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": QUERY_CLASSIFICATION_USER_PROMPT.format(
                        query=request.query,
                        language=settings.language,
                        tonality=settings.tonality
                    )
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
                    "content": GREET_USER_PROMPT.format(
                        query=request.query,
                        language=settings.language,
                        tonality=settings.tonality
                    )
                }
            )
            response = get_openai_response(
                messages=request.messages,
                is_json=False,
                max_tokens=settings.tokens
            )
            
        elif type == "cost_effective_analysis":
            articles_context, articles = retreive_articles(request.query)

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
                        articles_context=articles_context,
                        language=settings.language,
                        tonality=settings.tonality   
                    )
                }
            )
            response = get_openai_response(
                messages=messages,
                is_json=True
            )
            response = json.loads(response)
            articles_details = response['articles']

            article_map = {article["article_id"]: article["abstract"] for article in articles}

            for detail in articles_details:
                detail["abstract"] = article_map.get(detail["article_id"], "No abstract found")

            query_id = "query_"+str(uuid.uuid4())

            pie_chart = response['pie_chart']
            bar_chart = response['bar_chart']

            insert_query_history(
                request.user_id, 
                query_id, 
                request.query, 
                articles_details,
                pie_chart,
                bar_chart
            )
            
        else:
            chunks = retrieve_chunks(
                namespace=request.user_id,
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
                        query=request.query,
                        language=settings['language'],
                        tonality=settings['tonality']
                    )
                }
            )
            response = get_openai_response(
                messages=request.messages,
                is_json=False,
                max_tokens=settings.tokens
            )

        return JSONResponse(content={"message": response, "is_graph": type == "cost_effective_analysis"})
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
    
@log_performance
@router.post("/bubble_graph_details", response_model=BubbleGraphDetailsResponse)
async def bubble_graph_details_api(request: BubbleGraphDetailsRequest):
    """
    This API is used to retrieve the bubble graph details from the database.

    Args:
        request: BubbleGraphDetailsRequest

    Returns:
        BubbleGraphDetailsResponse
    """
    try:
        modality_count , articles_details = retreive_modality_count(request.query_id)
        return JSONResponse(content={"modality_count": modality_count, "articles_details": articles_details})
    except Exception as e:
        logger.error(f"Error in bubble graph details router: {traceback.format_exc()}")
        return JSONResponse(content={"message": f"Internal Server Error {e}"}, status_code=500)

@log_performance
@router.post("/get_descriptive_analysis", response_model=DescriptiveAnalysisResponse)
async def get_descriptive_analysis_api(request: DescriptiveAnalysisRequest):
    """
    This API is used to retrieve the descriptive analysis from the database.

    Args:
        request: DescriptiveAnalysisRequest

    Returns:
        DescriptiveAnalysisResponse
    """
    try:
        pie_chart , bar_chart = retrieve_descriptive_analysis(request.query_id)
        return JSONResponse(content={"pie_chart": pie_chart, "bar_chart": bar_chart})
    except Exception as e:
        logger.error(f"Error in get descriptive analysis router: {traceback.format_exc()}")
        return JSONResponse(content={"message": f"Internal Server Error {e}"}, status_code=500)

@log_performance
@router.post("/save_settings", response_model=SaveSettingsResponse)
async def save_settings_api(request: SaveSettingsRequest):
    """
    Save chatbot settings for a user
    
    Args:
        request: SaveSettingsRequest - Request containing user_id and settings
        
    Returns:
        SaveSettingsResponse - Success message
    """
    try:
        result = save_chatbot_settings(
            user_id=request.user_id,
            tonality=request.settings.tonality,
            language=request.settings.language,
            use_knowledge_base=request.settings.use_knowledge_base,
            tokens=request.settings.tokens
        )

        if result:  
            return JSONResponse(
                status_code=200,
                content={"message": "Settings saved successfully"}
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"message": "Failed to save settings"}
            )
    except Exception as e:
        logger.error(f"Error saving settings: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error saving settings: {str(e)}"}
        )

@log_performance
@router.post("/get_settings", response_model=GetSettingsResponse)
async def get_settings_api(request: GetSettingsRequest):
    """
    Get chatbot settings for a user
    
    Args:
        request: GetSettingsRequest - Request containing user_id
        
    Returns:
        GetSettingsResponse - Chatbot settings
    """
    try:
        settings = get_chatbot_settings(request.user_id)
        return JSONResponse(content={"settings": settings}, status_code=200)
    except Exception as e:
        logger.error(f"Error in get settings router: {traceback.format_exc()}")
        return JSONResponse(content={"message": f"Internal Server Error {e}"}, status_code=500)
    

@log_performance
@router.post("/get_latest_relevant_publications", response_model=GetLatestRelevantPublicationsResponse)
async def get_latest_relevant_publications_api(request: GetLatestRelevantPublicationsRequest):
    """
    Get latest relevant publications for a user
    """
    try:
        saved_articles_ids = get_saved_articles_ids(request.user_id)

        articles_details = get_articles_from_query_history(saved_articles_ids)

        lastest_relevant_publications =  []

        for article in articles_details:
            _ , latest_relevant_publications = retreive_articles(article[8], article[7])
            lastest_relevant_publications.extend(latest_relevant_publications)
        
        return JSONResponse(content={"lastest_relevant_publications": lastest_relevant_publications})
    except Exception as e:
        logger.error(f"Error in get latest relevant publications router: {traceback.format_exc()}")
        return JSONResponse(content={"message": f"Internal Server Error {e}"}, status_code=500)
