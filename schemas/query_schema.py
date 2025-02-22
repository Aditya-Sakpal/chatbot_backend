from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    user_id: str
    session_id: str
    messages : list

class QueryResponse(BaseModel):
    message: str