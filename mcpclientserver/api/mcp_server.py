from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import json
import os
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Any

load_dotenv()

mcp = FastMCP("docs")

USER_AGENT = "docs-app/1.0"
SERPER_URL = "https://google.serper.dev/search"

docs_urls = {
    "langchain": "python.langchain.com/docs",
    "llama-index": "docs.llamaindex.ai/en/stable",
    "openai": "platform.openai.com/docs",
}

async def search_web(query: str) -> dict:
    """Search web with better error handling"""
    payload = json.dumps({"q": query, "num": 2})
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SERPER_URL, headers=headers, data=payload, timeout=10.0  # Reduced timeout
            )
            response.raise_for_status()
            return response.json()
        except (httpx.TimeoutException, httpx.HTTPError) as e:
            print(f"Search error: {e}")
            return {"organic": []}

async def fetch_url_safe(url: str, max_chars: int = 10000) -> str:
    """Fetch URL with better error handling and content limiting"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url, 
                timeout=15.0,  # Reasonable timeout
                headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            
            # Parse and clean content
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and limit length
            text = soup.get_text(strip=True, separator='\n')
            
            # Limit content length to prevent huge responses
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[Content truncated...]"
            
            return f"URL: {url}\nContent:\n{text}\n{'-'*50}\n"
            
        except Exception as e:
            return f"URL: {url}\nError: Failed to fetch - {str(e)}\n{'-'*50}\n"

async def fetch_urls_concurrent(urls: List[str], max_chars: int = 10000) -> str:
    """Fetch multiple URLs concurrently with timeout protection"""
    try:
        # Use asyncio.wait_for to add an overall timeout
        tasks = [fetch_url_safe(url, max_chars) for url in urls]
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=25.0  # Overall timeout for all requests
        )
        
        # Combine results
        combined_text = ""
        for result in results:
            if isinstance(result, str):
                combined_text += result
            else:
                combined_text += f"Error processing URL: {str(result)}\n{'-'*50}\n"
        
        return combined_text
        
    except asyncio.TimeoutError:
        return "Error: Request timed out while fetching documentation pages"

@mcp.tool()  
async def get_docs(query: str, library: str):
    """
    Search the latest docs for a given query and library.
    Supports langchain, openai, and llama-index.

    Args:
        query: The query to search for (e.g. "Chroma DB")
        library: The library to search in (e.g. "langchain")

    Returns:
        Text from the docs (limited to prevent timeouts)
    """
    if library not in docs_urls:
        return f"Error: Library '{library}' not supported. Available: {list(docs_urls.keys())}"
    
    # Search for relevant docs
    search_query = f"site:{docs_urls[library]} {query}"
    print(f"Searching: {search_query}")
    
    results = await search_web(search_query)
    
    if not results.get("organic"):
        return f"No results found for '{query}' in {library} documentation"
    
    # Extract URLs
    urls = [result["link"] for result in results["organic"]]
    print(f"Found {len(urls)} URLs to fetch")
    
    # Fetch content concurrently
    content = await fetch_urls_concurrent(urls, max_chars=5000)  # Reduced max chars
    
    if not content.strip():
        return f"Found {len(urls)} results but could not fetch content"
    
    return content

@mcp.tool()
async def search_docs_only(query: str, library: str):
    """
    Just search for docs URLs without fetching content (faster).
    
    Args:
        query: The query to search for
        library: The library to search in
        
    Returns:
        Search results with titles and URLs
    """
    if library not in docs_urls:
        return f"Error: Library '{library}' not supported. Available: {list(docs_urls.keys())}"
    
    search_query = f"site:{docs_urls[library]} {query}"
    results = await search_web(search_query)
    
    if not results.get("organic"):
        return f"No results found for '{query}' in {library} documentation"
    
    output = f"Found {len(results['organic'])} results for '{query}' in {library}:\n\n"
    for i, result in enumerate(results["organic"], 1):
        output += f"{i}. {result.get('title', 'No title')}\n"
        output += f"   URL: {result['link']}\n"
        if result.get('snippet'):
            output += f"   Description: {result['snippet']}\n"
        output += "\n"
    
    return output

if __name__ == "__main__":
    mcp.run(transport="stdio")