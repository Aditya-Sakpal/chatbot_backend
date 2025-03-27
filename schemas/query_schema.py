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

class BubbleGraphDetailsRequest(BaseModel):
    query_id: str

class BubbleGraphDetailsResponse(BaseModel):
    data: list[dict]

class DescriptiveAnalysisRequest(BaseModel):
    query_id: str

class DescriptiveAnalysisResponse(BaseModel):
    data: dict
