import requests
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class searchParameters(BaseModel):
    query: str = Field(..., description="The search query to find relevant documents.")


class searchResult(BaseModel):
    title: str = Field(..., description="The title of the document.")
    link: str = Field(..., description="The link to the document.")
    snippet: str = Field(..., description="A snippet of the document content.")

    def to_string(self) -> str:
        return f"Title: {self.title}\nLink: {self.link}\nSnippet: {self.snippet}"
    
class funcitonCalling(BaseModel):
    function_name: str = Field(..., description="The name of the function to call.")
    parameters: Dict[str, Any] = Field(..., description="The parameters to pass to the function.")


