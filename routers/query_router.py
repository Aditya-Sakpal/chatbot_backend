import traceback
import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from schemas.query_schema import QueryRequest, QueryResponse
from utils.logger import log_performance, logger
from utils.openai_funcs import get_openai_response
from utils.constants import QUERY_CLASSIFICATION_USER_PROMPT, QUERY_CLASSIFICATION_SYSTEM_PROMPT, GREET_USER_PROMPT, GREET_SYSTEM_PROMPT, RESPONSE_GENERATION_USER_PROMPT, RESPONSE_GENERATION_SYSTEM_PROMPT
from utils.pinecone_funcs import retrieve_chunks

router = APIRouter()


@log_performance
@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
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

        return JSONResponse(content={"message": response})
    except Exception as e:
        logger.error(f"Error in query router: {traceback.format_exc()}")
        return JSONResponse(content={"message": "Internal Server Error"}, status_code=500)
