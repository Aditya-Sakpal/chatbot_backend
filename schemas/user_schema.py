from pydantic import BaseModel
from datetime import datetime
from fastapi import UploadFile, Form

class User(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: str
    created_at: datetime
    last_sign_in_at: datetime

class SaveArticles(BaseModel):
    user_id: str
    article_ids: list[str]

class GetArticlesAbstract(BaseModel):
    article_ids: list[str]

class SendEmailRequest:
    def __init__(
        self,
        pdf_file: UploadFile,
        user_id: str = Form(...),
        query: str = Form(...)
    ):
        self.pdf_file = pdf_file
        self.user_id = user_id
        self.query = query