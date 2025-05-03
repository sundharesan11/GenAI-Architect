from data_models import functionCalling, searchParameters
from typing import Optional, Dict, Any, List
import json
import ollama
from search_function import google_search


# Model name
MODEL_NAME = "gemma:7b"

def parse_function_call(response: str) -> Optional[functionCalling]:
    """Parse the model's response to extract function calls"""
    try:
        # Clean the response and find JSON structure
        response = response.strip()
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            return None
            
        json_str = response[start_idx:end_idx]
        data = json.loads(json_str)
        return functionCalling(**data)
    except Exception as e:
        print(f"Error parsing function call: {str(e)}")
        return None


# System message for the model
SYSTEM_MESSAGE = """You are an AI assistant with training data up to 2023. Answer questions directly when possible, and use search when necessary.

DECISION PROCESS:
1. For historical events (pre-2023):
   → Answer directly from your training data

2. For 2023 events:
   → If you have clear knowledge → Answer directly
   → If uncertain about details → Use search

3. For current events (post-2023):
   → Always use search

4. For timeless information (scientific facts, concepts, etc.):
   → Answer directly from your training data

IMPORTANT: ALWAYS USE SEARCH when the question:
- Contains terms like "current", "latest", "now", "present", "today", "recent"
- Asks about "who is" someone in a position that changes (champion, president, CEO, etc.)
- Requests information that might have changed since 2023
- Doesn't specify a time period for time-sensitive information

WHEN TO SEARCH:
- Events after 2023
- Uncertain details about 2023 events
- Current status of changing information
- Real-time data

FUNCTION CALL FORMAT:
When you need to search, respond WITH ONLY THE JSON OBJECT, no other text, no backticks:
{
    "name": "google_search",
    "parameters": {
        "query": "your search query"
    }
}

SEARCH FUNCTION:
{
    "name": "google_search",
    "description": "Search for real-time information",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search term"
            }
        },
        "required": ["query"]
    }
}

RESPONSE GUIDELINES:
1. Only include facts from search results
2. Never add dates not in search results
3. No assumptions about timing or events
4. Quote dates exactly as they appear
5. Keep responses concise and factual"""

def process_message(user_input, chat_history):
    """Process user message and update chat history"""
    try:
        # First, add user message to history for display
        chat_history.append({"role": "user", "content": user_input})
        search_info = None
        
        # Get response from model
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_input}
            ]
        )
        
        # Get the model's response
        model_response = response['message']['content']
        
        # Try to parse the response as a function call
        function_call = parse_function_call(model_response)
        
        if function_call and function_call.name == "google_search":
            # Validate search parameters
            search_params = searchParameters(**function_call.parameters)
            search_query = search_params.query
            
            # Add search info to history
            search_info = f"🔍 Searching for: {search_query}"
            chat_history.append({"role": "assistant", "content": search_info})
            yield chat_history
            
            # Execute the search
            search_result = google_search(search_query)
            
            # Update search info with results
            search_info = f"🔍 Searched for: {search_query}\n\n📊 Result:\n{search_result.to_string()}"
            chat_history[-1] = {"role": "assistant", "content": search_info}
            yield chat_history
            
            # Get final response from model with search results
            final_response = ollama.chat(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_MESSAGE},
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": model_response},
                    {"role": "user", "content": f"Based on the search results: {search_result.to_string()}"}
                ]
            )
            
            assistant_response = final_response['message']['content']
        else:
            # If no function call, return the direct response
            assistant_response = model_response
        
        # Update final response in history
        if search_info:
            # Add both search info and final response
            chat_history.append({"role": "assistant", "content": f"✨ Response:\n{assistant_response}"})
        else:
            # Just add assistant response
            chat_history.append({"role": "assistant", "content": assistant_response})
        
        yield chat_history
            
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        chat_history.append({"role": "assistant", "content": error_msg})
        yield chat_history