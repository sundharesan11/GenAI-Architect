from typing import Optional, List
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from datetime import datetime
import json
import os
from utils.logger import logger

from anthropic import Anthropic
from anthropic.types import Message, ToolCall

class MCPClient:
    # Initialize the session and objects
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.llm = Anthropic()
        self.tools = []
        self.messages = []
        self.logger = logger

    # Connect to an MCP server
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        try: 
            is_python = server_script_path.endswith('.py')
            is_js = server_script_path.endswith('.js')
            if not (is_python or is_js):
                raise ValueError("Server script must be a .py or .js file")

            command = "python" if is_python else "node"
            server_params = StdioServerParameters(
                command=command,
                args=[server_script_path],
                env=None
            )

            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

            await self.session.initialize()

            self.logger.info(f"Connected to MCP server: {server_script_path}")
        
            mcp_tools = await self.get_mcp_tools()
            if mcp_tools:
                self.tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    for tool in mcp_tools
                ]

            self.logger.info(f"Available tools: {self.tools}")

        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            raise

    # Get mcp tools lists
    async def get_mcp_tools(self) -> List[ToolCall]:
        """Get the list of MCP tools from the server."""
        if not self.session:
            self.logger.error("Not connected to MCP server")
            return []

        try:
            response = await self.session.list_tools()
            self.logger.info(f"Retrieved MCP tools: {response.tools}")
            return response.tools
        except Exception as e:
            self.logger.error(f"Failed to retrieve MCP tools: {e}")
            return []
        
    # Process query
    async def process_query(self, query: str) -> str:
        try:
            self.logger.info(f"Processing query: {query}")
            user_message = {"role": "user", "content": query}
            self.messages = [user_message]

            while True:
                response = await self.call_llm()

                # The response is "text"
                if response.content[0].type == "text" and len(response.content) == 1:
                    assistant_message = {
                        "role": "assistant",
                        "content": response.content[0].text
                    }
                    self.messages.append(assistant_message)
                    break

                # The response is a tool call
                assistant_message = {
                    "role": "assistant",
                    "content": response.to_dict()["content"],
                }
                self.messages.append(assistant_message)

                for content in response.content:
                    if content.type == "text":
                        self.messages.append({
                            "role": "assistant",
                            "content": content.text
                        })
                    elif content.type == "tool_call":
                        tool_name = content.name
                        tool_args = content.input
                        tool_use_id = content.id
                        self.logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
                        try:
                            result = await self.session.call_tool(tool_name, tool_args, tool_use_id)
                            self.logger.info(f"Tool {tool_name} returned: {result[:100]}...")
                            self.messages.append({
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use_id,
                                        "content": result.content,
                                    }
                                ]
                                })
                        except Exception as e:
                            self.logger.error(f"Error calling tool {tool_name}: {e}")
                            raise
            return self.messages
        
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            raise

    # Call the LLM
    async def call_llm(self):
        try:
            self.logger.info("Calling LLM")
            return self.llm.messages.create(
                model = "claude-3-5-haiku-20241022",
                max_tokens = 1000,
                messages = self.messages,
                tools = self.tools,
            )
        except Exception as e:
            self.logger.error(f"Error calling LLM: {e}")
            raise

    # cleanup
    async def cleanup(self):
        try:
            await self.exit_stack.aclose()
            self.logger.info("Disconnected from MCP server")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            raise