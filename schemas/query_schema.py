from pydantic import BaseModel, Field

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

class ChatbotSettings(BaseModel):
    tonality: int
    language: str
    use_knowledge_base: bool
    tokens: int
    
class QueryRequest(BaseModel):
    query: str
    user_id: str
    messages: list[dict]
    settings: ChatbotSettings

class SaveSettingsRequest(BaseModel):
    user_id: str
    settings: ChatbotSettings

class SaveSettingsResponse(BaseModel):
    message: str

class GetSettingsRequest(BaseModel):
    user_id: str

class GetSettingsResponse(BaseModel):
    settings: ChatbotSettings

class GetLatestRelevantPublicationsRequest(BaseModel):
    user_id: str

class GetLatestRelevantPublicationsResponse(BaseModel):
    lastest_relevant_publications: list[dict]

