from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import json
import os
from bs4 import BeautifulSoup
load_dotenv()


mcp = FastMCP("searchdocs")

USER_AGENT = "searchdocs-app/1.0"
SERPER_URL = "https://google.serper.dev/search"

docs_urls = {
    "langchain": "python.langchain.com/docs",
    "llama-index": "docs.llamaindex.ai/en/stable",
    "openai": "platform.openai.com/docs",
}

async def search_web(query: str) -> dict | None:
    """Search the web using Serper API."""

    payload = json.dumps({
        "q": query,
        "num": 2
    })

    headers = {
        "User-Agent": USER_AGENT,
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
    }
    
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(SERPER_URL, headers=headers, data=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            print("Request timed out. Please try again later.")
            return {"timeout":[]}
        
async def fetch_url(url: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            return text
        except httpx.TimeoutException:
            print("Request timed out. Please try again later.")
            return {"timeout":[]}
