
from data_models import searchResult, searchParameters
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

# Get Serper API key from environment variables
# Create a .env file with SERPER_API_KEY=your_api_key (do not commit .env to GitHub)
SERPER_API_KEY = os.getenv('SERPER_API_KEY')
if not SERPER_API_KEY:
    raise ValueError("Serper API key not found. Please set SERPER_API_KEY in your .env file.")


def google_search(query: str) -> searchResult:
    """Perform a Google search using Serper.dev API"""
    try:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        results = response.json()
        
        if not results.get('organic'):
            raise ValueError("No search results found.")
            
        first_result = results['organic'][0]
        return searchResult(
            title=first_result.get('title', 'No title'),
            link=first_result.get('link', 'No link'),
            snippet=first_result.get('snippet', 'No snippet available.')
        )
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise



