from pydantic import BaseModel, Field

class ScrapeSingleUrlRequest(BaseModel):
    url: str
    user_id: str

class ScrapeSingleUrlResponse(BaseModel):
    job_id: str
    status: str
    url: str
    message: str

class WebCrawlRequest(BaseModel):
    url: str
    user_id: str
    depth: int = Field(default=1, ge=1, le=5, description="Number of pages to crawl (1-5)")

class WebCrawlResponse(BaseModel):
    job_id: str
    status: str
    url: str
    message: str

class WebCrawlStatusRequest(BaseModel):
    job_id: str
    user_id: str

class WebCrawlStatusResponse(BaseModel):
    job_id: str
    status: str

class FetchSinglePageUrlsRequest(BaseModel):
    user_id: str

class FetchSinglePageUrlsResponse(BaseModel):
    user_id: str
    urls: list[str]

class FetchWebCrawlUrlsRequest(BaseModel):
    user_id: str

class FetchWebCrawlUrlsResponse(BaseModel):
    user_id: str
    urls: list[str]

class FetchDocumentsRequest(BaseModel):
    user_id: str

class FetchDocumentsResponse(BaseModel):
    documents: list[str]

