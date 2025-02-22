import os

from dotenv import load_dotenv
from pinecone.grpc import PineconeGRPC as Pinecone

from utils.openai_funcs import get_embeddings

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

def retrieve_chunks(
    namespace: str,
    query: str,
    num_results: int = 5
):
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
        print("Error: ", e)
        return None