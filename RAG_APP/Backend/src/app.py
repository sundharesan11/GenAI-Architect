from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.rag import get_answer_and_docs
from src.qdrant import upload_website_to_collection


app = FastAPI(
    title="RAG API",
    description="A simple API for RAG",
    version="0.1.0"
)

@app.get("/", description="Root endpoint")
def root():
    return JSONResponse(content={"message": "Hello, World!"}, status_code=200)


@app.post("/chat", description="Chat with the RAG API")
def chat(message: str):
    response = get_answer_and_docs(message)
    response_content = {
        "Question": message,
        "Answer": response["answer"],
        "Documents": response["context"]
    }
    return JSONResponse(content=response_content, status_code=200)


@app.post("/indexing", description= "Index a website through this endpoint")
def indexing(url:str):
    try: 
        response = upload_website_to_collection(url)
        return JSONResponse(content={"url": response}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code = 500)