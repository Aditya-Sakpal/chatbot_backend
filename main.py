from fastapi import FastAPI

from routers.query_router import router as query_router

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

app.include_router(query_router, prefix="/api/v1", tags=["query"])