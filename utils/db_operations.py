import os
import traceback
from datetime import datetime
import uuid

import psycopg2
from dotenv import load_dotenv

from utils.logger import logger

load_dotenv()

def connect_to_db():
    """
    Connect to the database and return the connection object

    Returns:
        conn: psycopg2.connection
    """ 
    try:
        conn = psycopg2.connect(os.getenv("DB_URL"))
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise e

def create_user(
    user_id: str,
    first_name: str,
    last_name: str,
    email: str,
    created_at: datetime,
    last_sign_in_at: datetime
):
    """
    Create a new user in the database

    Args:
        user_id: str
        first_name: str
        last_name: str
        email: str

    Returns:
        object: {"message": "User created successfully"}
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, first_name, last_name, email, created_at, last_signed_in_at) VALUES (%s, %s, %s, %s, %s, %s)", 
                       (user_id, first_name, last_name, email, created_at, last_sign_in_at))
        conn.commit()
        logger.info(f"User created successfully: {user_id}")
        return {"message": "User created successfully"}
    except Exception as e:
        logger.error(f"Error creating user: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def insert_query_history(
    user_id: str,
    query_id: str,
    query: str,
    articles: list[dict]
):
    """
    This API is used to insert the query history into the database.

    Args:
        user_id: str
        query_id: str
        query: str
        articles: list[dict]

    Returns:
        object: {"message": "Query entered successfully"}
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        for article in articles:  
            article_id = "article_"+str(uuid.uuid4())
            cursor.execute("INSERT INTO query_history (query_id, user_id, article_id ,article_title, modality, organ, disease, result, year) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                           (query_id, user_id, article_id, article['title'], article['modality'], article['organ'], article['disease'], article['result'], article['year']))

        conn.commit()
        logger.info(f"Query entered successfully: {query}")
        return {"message": "Query entered successfully"}
    except Exception as e :
        logger.error(f"Error entering query: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def retrieve_query_history(
    user_id: str
):
    """
    This API is used to retrieve the query history from the database.

    Args:
        user_id: str

    Returns:
        list[dict]: List of query history
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM query_history WHERE user_id = %s", (user_id,))
        query_history = cursor.fetchall()
        return query_history
    except Exception as e:  
        logger.error(f"Error retrieving query history: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

