from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from src.rag import get_answer_and_docs
from src.qdrant import upload_website_to_collection
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI(
    title="RAG API",
    description="A simple API for RAG",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    message: str

class IndexingRequest(BaseModel):
    url: str

@app.get("/", description="Root endpoint")
def root():
    return JSONResponse(content={"message": "Hello, World!"}, status_code=200)


@app.post("/chat", description="Chat with the RAG API")
def chat(message: Message):
    response = get_answer_and_docs(message.message)
    response_content = {
        "Question": message.message,
        "Answer": response["Answer"],
        "Documents": response["Documents"]
    }
    return JSONResponse(content=response_content, status_code=200)


@app.post("/indexing", description= "Index a website through this endpoint")
async def indexing(data: IndexingRequest):
    try:
        response = upload_website_to_collection(data.url)
        return JSONResponse(content={"url": response}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
# def indexing(data: dict = Body(...)):
#     try: 
#         url = data.get("url")
#         if not url:
#             return JSONResponse(content={"error": "URL is required"}, status_code=400)

#         response = upload_website_to_collection(url)
#         return JSONResponse(content={"url": response}, status_code=200)
#     except Exception as e:
#         logging.error(f"Error during website indexing: {str(e)}")
#         return JSONResponse(content={"error": str(e)}, status_code = 500)