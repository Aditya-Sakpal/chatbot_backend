import traceback

from utils.initialize import splitter
from llama_index.core import Document

from utils.logger import logger


def get_chunks(text: str):
    """
    Get chunks from text using semantic splitter
    Args:
        text: str
    Returns:
        list of chunks
    """
    try:
        if len(text) > 7000:
            texts = []
            for i in range(0, len(text), 7000):
                texts.append(text[i:i+7000])
        else:
            texts = [text]
        
        documents = splitter.get_nodes_from_documents([Document(text=text) for text in texts])
        chunks = []
        for doc in documents:
            chunks.append(doc.text)
        return chunks
    except Exception as e:
        logger.error(f"Error getting chunks: {traceback.format_exc()}")
        raise e