from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from contextlib import asynccontextmanager
from mcp_client import MCPClient
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()