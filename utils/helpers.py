import traceback
import xml.etree.ElementTree as ET
from typing import Optional

import requests

from utils.logger import logger

from utils.constants import articles_search_url,articles_fetch_url
from utils.db_operations import connect_to_db

def retreive_articles(
    query : str,
    article_id_for_duplicacy_check : Optional[str] = None
):
    """
    Retrieve articles from PubMed based on the query provided
    
    Args:
    query : str : Query to search for articles
    
    Returns:
    articles_context : str : Context of the articles retrieved
    """
    try:
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": "10",  
            "retmode": "xml"
        }
        search_response = requests.get(articles_search_url, params=search_params)
        
        search_root = ET.fromstring(search_response.content)

        uids = [uid.text for uid in search_root.findall(".//Id")]

        fetch_params = {
            "db": "pubmed",
            "id": ",".join(uids),
            "retmode": "xml"
        }
        fetch_response = requests.get(articles_fetch_url, params=fetch_params)
        fetch_root = ET.fromstring(fetch_response.content)
        
        articles_context = ""
        articles = []
        for article in fetch_root.findall(".//PubmedArticle"):
            article_dict = {}
            article_id = article.find(".//ArticleId").text

            if article_id_for_duplicacy_check is not None and article_id == article_id_for_duplicacy_check:
                continue
            
            articles_context += "Article ID : " + article_id + "\n"
            article_dict['article_id'] = article_id
            title = article.find(".//ArticleTitle").text
            articles_context += "Article Title : " + title + "\n"
            article_dict['title'] = title
            logger.info(f"Title : {title}") 

            abstract = article.findall(".//AbstractText")
            article_dict['abstract'] = ""
            if abstract is not None :
                articles_context += "Abstract : "
                for text in abstract:
                    if text.text is not None:
                        articles_context += text.text 
                        article_dict['abstract'] += text.text
            else:
                logger.info("Abstract not found")
            
            articles_context += "\n\n"
            articles.append(article_dict)
        return articles_context , articles
    except Exception as e :
        logger.error(f"Error in retrieving articles : {traceback.format_exc()}")
        raise e
    
def retreive_modality_count(
    query_id : str
):
    """
    Retrieve modality count from the database

    Args:
        query_id : str : Query ID

    Returns:
        modality_count : list[dict] : Modality count
    """
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM query_history WHERE query_id = %s", (query_id,))
        bubble_graph_details = cursor.fetchall()

        modality_count = {}
        articles_details = []
        for detail in bubble_graph_details:
            modality_count[detail[1]] = modality_count.get(detail[1], 0) + 1
            articles_details.append({'article_id': detail[7], 'article_title': detail[8]})

        modality_count = sorted(modality_count.items(), key=lambda x: x[1], reverse=True)

        return modality_count , articles_details
    except Exception as e:
        logger.error(f"Error in retrieving bubble graph details : {traceback.format_exc()}")
        raise e
    finally:
        cursor.close()
        conn.close()


