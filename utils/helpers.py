import traceback
import xml.etree.ElementTree as ET

import requests

from utils.logger import logger

from utils.constants import articles_search_url,articles_fetch_url

def retreive_articles(
    query : str
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
        
        for article in fetch_root.findall(".//PubmedArticle"):
            title = article.find(".//ArticleTitle").text
            articles_context += "Article Title : " + title + "\n"
            logger.info(f"Title : {title}") 

            abstract = article.findall(".//AbstractText")

            if abstract is not None :
                articles_context += "Abstract : "
                for text in abstract:
                    articles_context += text.text 
            else:
                logger.info("Abstract not found")
            
            articles_context += "\n\n"
        
        return articles_context
    except Exception as e :
        logger.error(f"Error in retrieving articles : {traceback.format_exc()}")
        raise e