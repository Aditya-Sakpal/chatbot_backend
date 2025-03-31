import os
import traceback
from datetime import datetime
import json 
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
        print(os.getenv("DB_URL"),type(os.getenv("DB_URL")))
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
    articles_details: list[dict],
    pie_chart: dict,
    bar_chart: dict
):
    """
    This API is used to insert the query history into the database.

    Args:
        user_id: str
        query_id: str
        query: str
        articles_details: list[dict]
        pie_chart: dict
        bar_chart: dict

    Returns:
        object: {"message": "Query entered successfully"}
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        for article in articles_details:  
            cursor.execute("INSERT INTO query_history (query_id, query, user_id, article_id ,article_title, abstract, modality, organ, disease, result, year , pie_chart, bar_chart) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                           (query_id, query, user_id, article['article_id'], article['title'], article['abstract'], article['modality'], article['organ'], article['disease'], article['result'], article['year'], json.dumps(pie_chart), json.dumps(bar_chart)))

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

def save_articles(user_id: str, article_ids: list[str]):
    """
    Save articles in the database.
    If the user already exists, append new article_ids while ensuring uniqueness.
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT saved_article_ids FROM saved_articles WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if result:
            # User exists, merge article_ids with existing ones
            existing_article_ids = set(result[0])  # Convert array to set for uniqueness
            new_article_ids = set(article_ids)  # Convert input list to set
            updated_article_ids = list(existing_article_ids | new_article_ids)  # Merge and remove duplicates

            cursor.execute(
                "UPDATE saved_articles SET saved_article_ids = %s WHERE user_id = %s",
                (updated_article_ids, user_id)
            )
        else:
            # User does not exist, insert new record
            cursor.execute(
                "INSERT INTO saved_articles (user_id, saved_article_ids) VALUES (%s, %s)",
                (user_id, article_ids)
            )
        
        conn.commit()
        return {"message": "Articles saved successfully"}

    except Exception as e:
        print(f"Error saving articles: {traceback.format_exc()}")
        raise e

    finally:
        cursor.close()
        conn.close()

def get_articles_abstract(
    article_ids: list[str]
):
    """
    Get saved articles from the database

    Args:
        article_ids: list[str]

    Returns:
        list[dict]: List of saved articles
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        abstract_dict = []

        for article_id in article_ids:
            article_data = {}
            cursor.execute("SELECT article_title, abstract FROM query_history WHERE article_id = %s", (article_id,))
            for article in cursor.fetchall():
                article_data['article_title'] = article[0]
                article_data['abstract'] = article[1]
            abstract_dict.append(article_data)

        return abstract_dict
    except Exception as e:
        logger.error(f"Error getting saved articles: {traceback.format_exc()}")
        raise e

def get_user_email(user_id: str) -> str:
    """
    Get user's email from the database

    Args:
        user_id: str

    Returns:
        str: User's email
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE user_id = %s", (user_id,))
        email = cursor.fetchone()
        if email:
            return email[0]
        return None
    except Exception as e:
        logger.error(f"Error getting user email: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def retrieve_descriptive_analysis(
    query_id: str
):
    """
    Retrieve descriptive analysis from the database

    Args:
        query_id: str

    Returns:
        tuple: (pie_chart, bar_chart)
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pie_chart, bar_chart 
            FROM query_history 
            WHERE query_id = %s""", (query_id,))
        pie_chart, bar_chart = cursor.fetchone()
        return pie_chart, bar_chart
    except Exception as e:
        logger.error(f"Error retrieving descriptive analysis: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def update_single_page_urls(user_id: str, url: str):
    """
    Append a URL to the single_page_urls array for a given user.
    
    Args:
        user_id (str): The user ID.
        url (str): The URL to be added.
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET single_page_urls = array_append(single_page_urls, %s)
            WHERE user_id = %s;
        """, (url, user_id))

        conn.commit()
        logger.info(f"URL added to single_page_urls for user {user_id}")
    except Exception as e:
        logger.error(f"Error updating single_page_urls: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def update_web_crawl_urls(user_id: str, url: str):
    """
    Append a URL to the web_crawl_urls array for a given user.
    This stores the initial URL that the user provided for web crawling.
    
    Args:
        user_id (str): The user ID.
        url (str): The URL to be added.
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET web_crawl_urls = array_append(web_crawl_urls, %s)
            WHERE user_id = %s;
        """, (url, user_id))

        conn.commit()
        logger.info(f"URL added to web_crawl_urls for user {user_id}")
    except Exception as e:
        logger.error(f"Error updating web_crawl_urls: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def create_crawling_job(user_id: str, url: str) -> str:
    """
    Create a new crawling job in the database
    
    Args:
        user_id (str): The user ID
        url (str): The URL to crawl
        
    Returns:
        str: The job ID
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        # Generate a unique job ID
        job_id = f"job_{uuid.uuid4()}"
        
        cursor.execute("""
            INSERT INTO crawling_jobs (job_id, user_id, url, status, created_at)
            VALUES (%s, %s, %s, 'pending', NOW())
        """, (job_id, user_id, url))


        
        conn.commit()
        logger.info(f"Created crawling job {job_id} for user {user_id}")
        return job_id
    except Exception as e:
        logger.error(f"Error creating crawling job: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def update_job_status(job_id: str, status: str, error_message: str = None):
    """
    Update the status of a crawling job
    
    Args:
        job_id (str): The job ID
        status (str): The new status ('pending', 'succeeded', 'failed')
        error_message (str, optional): Error message if status is 'failed'
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        if error_message:
            cursor.execute("""
                UPDATE crawling_jobs
                SET status = %s, error_message = %s, completed_at = NOW()
                WHERE job_id = %s
            """, (status, error_message, job_id))
        else:
            cursor.execute("""
                UPDATE crawling_jobs
                SET status = %s, completed_at = NOW()
                WHERE job_id = %s
            """, (status, job_id))
        
        conn.commit()
        logger.info(f"Updated job {job_id} status to {status}")
    except Exception as e:
        logger.error(f"Error updating job status: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def get_job_status(job_id: str, user_id: str) -> dict:
    """
    Get the status of a crawling job
    
    Args:
        job_id (str): The job ID
        user_id (str): The user ID
        
    Returns:
        dict: Job details including status
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT job_id, url, status, created_at, completed_at, error_message
            FROM crawling_jobs
            WHERE job_id = %s AND user_id = %s
        """, (job_id, user_id))
        
        job = cursor.fetchone()
        if job:
            return {
                "job_id": job[0],
                "url": job[1],
                "status": job[2],
                "created_at": job[3],
                "completed_at": job[4],
                "error_message": job[5]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting job status: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def get_single_page_urls(user_id: str) -> list[str]:
    """
    Get all single page URLs for a user
    
    Args:
        user_id (str): The user ID
        
    Returns:
        list[str]: List of single page URLs
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT single_page_urls
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        return result[0] if result and result[0] else []
    except Exception as e:
        logger.error(f"Error getting single page URLs: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def get_web_crawl_urls(user_id: str) -> list[str]:
    """
    Get all web crawl URLs for a user
    
    Args:
        user_id (str): The user ID
        
    Returns:
        list[str]: List of web crawl URLs
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT web_crawl_urls
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        return result[0] if result and result[0] else []
    except Exception as e:
        logger.error(f"Error getting web crawl URLs: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def check_user_exists(user_id: str) -> bool:
    """
    Check if a user already exists in the database
    
    Args:
        user_id (str): The user ID to check
        
    Returns:
        bool: True if user exists, False otherwise
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        logger.error(f"Error checking user existence: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def check_email_exists(email: str) -> bool:
    """
    Check if an email is already registered in the database
    
    Args:
        email (str): The email to check
        
    Returns:
        bool: True if email exists, False otherwise
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE email = %s
        """, (email,))
        
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        logger.error(f"Error checking email existence: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def update_user_documents(user_id: str, document_names: list[str]):
    """
    Append document names to the documents array for a given user.
    
    Args:
        user_id (str): The user ID
        document_names (list[str]): List of document names to add
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        # Convert list to array and append to existing documents
        cursor.execute("""
            UPDATE users
            SET documents = array_cat(documents, %s)
            WHERE user_id = %s;
        """, (document_names, user_id))

        conn.commit()
        logger.info(f"Documents added for user {user_id}")
    except Exception as e:
        logger.error(f"Error updating user documents: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def get_user_documents(user_id: str) -> list[str]:
    """
    Get all document names for a user
    
    Args:
        user_id (str): The user ID
        
    Returns:
        list[str]: List of document names
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT documents
            FROM users
            WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        return result[0] if result and result[0] else []
    except Exception as e:
        logger.error(f"Error getting user documents: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def save_chatbot_settings(
    user_id: str,
    tonality: int,
    language: str,
    use_knowledge_base: bool,
    tokens: int
):
    """
    Save or update chatbot settings for a user
    
    Args:
        user_id (str): The user ID
        tonality (int): Tonality value (1-5)
        language (str): Selected language
        use_knowledge_base (bool): Whether to use knowledge base
        tokens (int): Number of tokens
        
    Returns:
        dict: Success message
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        
        # Check if settings exist for user
        cursor.execute("""
            SELECT setting_id 
            FROM chatbot_settings 
            WHERE user_id = %s
        """, (user_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing settings
            cursor.execute("""
                UPDATE chatbot_settings
                SET tonality = %s,
                    language = %s,
                    use_knowledge_base = %s,
                    tokens = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (tonality, language, use_knowledge_base, tokens, user_id))
        else:
            # Insert new settings
            cursor.execute("""
                INSERT INTO chatbot_settings 
                (user_id, tonality, language, use_knowledge_base, tokens)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, tonality, language, use_knowledge_base, tokens))
            
        conn.commit()
        logger.info(f"Chatbot settings saved for user {user_id}")
        return {"message": "Settings saved successfully"}
    except Exception as e:
        logger.error(f"Error saving chatbot settings: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()


def get_chatbot_settings(user_id: str) -> dict:
    """
    Get chatbot settings for a user
    
    Args:
        user_id (str): The user ID

    Returns:
        dict: Chatbot settings
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tonality, language, use_knowledge_base, tokens
            FROM chatbot_settings
            WHERE user_id = %s
        """, (user_id,))

        settings = cursor.fetchone()    
        return {
            "tonality": settings[0],
            "language": settings[1],
            "use_knowledge_base": settings[2],
            "tokens": settings[3]
        }
    except Exception as e:
        logger.error(f"Error getting chatbot settings: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def get_saved_articles_ids(user_id: str) -> list[str]:
    """
    Get saved articles for a user
    """
    try:
        conn = connect_to_db()  
        cursor = conn.cursor()

        cursor.execute("""
            SELECT saved_article_ids
            FROM saved_articles
            WHERE user_id = %s
        """, (user_id,))

        result = cursor.fetchone()
        return result[0] if result and result[0] else []
    except Exception as e:  
        logger.error(f"Error in saved articles: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()

def get_articles_from_query_history(article_ids: list[str]) -> list[dict]:
    """
    Get articles from query history
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        # Ensure article_ids is a tuple for the IN clause
        query = """
            SELECT * FROM query_history WHERE article_id = ANY(%s)
        """
        cursor.execute(query, (article_ids,))  # Pass as a single-element tuple

        result = cursor.fetchall()
        return result
    except Exception as e:
        logger.error(f"Error in get articles from query history: {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()
