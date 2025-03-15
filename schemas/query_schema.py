from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    user_id: str
    messages : list

class QueryResponse(BaseModel):
    message: str

class QueryHistoryRequest(BaseModel):
    user_id: str

class QueryHistoryResponse(BaseModel):
    message: list[dict]
