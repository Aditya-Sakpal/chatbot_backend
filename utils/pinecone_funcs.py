import traceback

from utils.openai_funcs import get_embeddings
from utils.logger import logger
from utils.initialize import index 

def retrieve_chunks(
    namespace: str,
    query: str,
    num_results: int = 5
):
    """
    Retrieve chunks from Pinecone

    Args:
        namespace: str - The namespace to retrieve chunks from
        query: str - The query to retrieve chunks for 
        num_results: int - The number of results to retrieve

    Returns:
        list[str] - List of chunks
    """
    try:
        response = index.query(
            namespace=namespace,
            vector=get_embeddings(query),
            top_k=num_results,
            include_metadata=True,
            include_values=False
        )
        
        if response['matches'] is None or response['matches'] == []:
            return None
        
        if len(response['matches']) > 0:
            chunks = []
            for match in response['matches']:
                chunks.append(
                    match['metadata']['text']
                )
            return chunks          
    except Exception as e:
        logger.error(f"Error retrieving chunks: {traceback.format_exc()}")      
        raise e
    
def upsert_chunks(
    vectors: list[dict],
    user_id: str
):
    """
    Upsert chunks into Pinecone

    Args:
        vectors: list[dict] - List of vectors to upsert
        user_id: str - The user ID to upsert vectors to

    Returns:
        bool - True if vectors were upserted successfully, False otherwise
    """
    try:
        index.upsert(
            vectors=vectors,
            namespace=user_id,
            batch_size=100
        )
        return True
    except Exception as e:
        logger.error(f"Error upserting chunks: {traceback.format_exc()}")
        raise e

def transfer_vectors_from_default_namespace(
    user_id: str
):
    """
    Transfer all vectors from the default namespace to a new namespace for a user

    Args:
        user_id: str - The user ID to transfer vectors to

    Returns:
        bool - True if vectors were transferred successfully, False otherwise
    """
    try:
        vector_ids = list(index.list(namespace='chatbot'))

        all_vectors = {}

        for i in range(len(vector_ids)):
            batch_ids = vector_ids[i]
            response = index.fetch(batch_ids, namespace='chatbot')
            all_vectors.update(response.vectors)

        namespace = user_id

        #all_vectors is a dictionary of vector ids and their corresponding vectors
        #we need to convert it to a list of dictionaries
        
        vectors = []
        for vector_id, vector in all_vectors.items():
            vectors.append({
                "id": vector_id,
                "values": vector.values,
                "metadata": vector.metadata
            })

        index.upsert(
            vectors=vectors,
            namespace=namespace,
            batch_size=100
        )
        return True
    except Exception as e:
        logger.error(f"Error transferring vectors from default namespace: {traceback.format_exc()}")
        raise e
