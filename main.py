from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.query_router import router as query_router
from routers.users_router import router as users_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

app.include_router(query_router, prefix="/api/v1", tags=["query"])
app.include_router(users_router, prefix="/api/v1", tags=["users"])