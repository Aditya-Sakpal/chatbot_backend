from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: str
    created_at: datetime
    last_sign_in_at: datetime
