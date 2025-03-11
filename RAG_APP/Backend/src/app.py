from fastapi import FastAPI
from fastapi.responses import JSONResponse

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
    return JSONResponse(content={"message": message}, status_code=200)


