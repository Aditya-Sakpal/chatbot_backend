import os 
import traceback

from dotenv import load_dotenv
from openai import OpenAI
from utils.logger import logger

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def get_embeddings(
    text : str
):
    """
    This function gets the embeddings of the text
    
    Args:
        text : str : The text for which embeddings are to be generated
        
    Returns:
        embeddings : list : The embeddings of the text as a list
    """
    try:
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error in get_embeddings: {traceback.format_exc()}")
        return {"error": f"Internal Server Error {e}"}

def get_openai_response(
    messages : list ,
    is_json : bool = False
):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            response_format={ "type": "json_object" } if is_json else None
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in get_openai_response: {traceback.format_exc()}")
        return {"error": f"Internal Server Error {e}"}