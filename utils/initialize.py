import os

from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI
from llama_index.core.node_parser import (
    SemanticSplitterNodeParser,
)
from llama_index.embeddings.openai import OpenAIEmbedding

load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")  
os.environ['PINECONE_API_KEY'] = os.getenv("PINECONE_API_KEY")

pc = Pinecone()
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))
embed_model = OpenAIEmbedding()
splitter = SemanticSplitterNodeParser(
    include_metadata=True,
    buffer_size=1, 
    breakpoint_percentile_threshold=95, 
    embed_model=embed_model
)
openai_client = OpenAI()