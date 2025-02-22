import json
import os

from openai import OpenAI
from dotenv import load_dotenv
from llama_index.core import Document
from llama_index.core.node_parser import (
    SemanticSplitterNodeParser,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from pinecone import Pinecone

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")


index = pc.Index(
    name="chatbot",
    host=os.getenv("PINECONE_INDEX_HOST")
)

embed_model = OpenAIEmbedding()
splitter = SemanticSplitterNodeParser(
    include_metadata=True,
    buffer_size=1, 
    breakpoint_percentile_threshold=95, 
    embed_model=embed_model
)

client = OpenAI()

with open('D:/chatbot_backend/ingestion/data/finalData.json', encoding='utf-8') as f:
    data = json.load(f)

documents = []
for item in data:
    print("Processing item: ", item['url'])
    doc = Document(
        text=item['abstract'],
        metadata={
            'url': item['url'],
            'heading': item['headings'] if 'headings' in item else '',
            'text': item['abstract']
        }
    )
    documents.append(doc)

def get_embeddings(text):
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return response.data[0].embedding

vectors = []
nodes = splitter.get_nodes_from_documents(documents)
for idx, node in enumerate(nodes):
    print("Processing node: ", idx)
    embeddings = get_embeddings(node.text)
    vectors.append({
        "id":str(idx),
        "values":embeddings,
        "metadata":node.metadata
    })

index.upsert(
    vectors=vectors,
    namespace="chatbot",
    batch_size=100
)