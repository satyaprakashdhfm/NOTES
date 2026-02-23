from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse
from pydantic import BaseModel, Field
from collections.abc import AsyncIterable
from typing import Annotated, Any, Literal, List
from typing_extensions import TypedDict
from rich.pretty import pprint
import asyncio, os
from uuid import uuid4
from agno.db.sqlite import SqliteDb
from agno.models.ollama import Ollama
from agno.agent import Agent, RunOutput
from agno.tools.mcp import MCPTools
from agno.models.aws import AwsBedrock
load_dotenv()

llm = AwsBedrock(
    id="amazon.nova-lite-v1:0", 
    aws_region="us-east-1", 
    temperature=0.9
)

class McpAgent:
    def __init__(self, tools, path: str = ''):
        self.model = llm
        self.tools = tools
        self.agent = self.get_agent(path)
    
    def handle_errors(self, e: ValueError) -> str:
        return "Invalid input provided"
    
    def get_agent(self, path: str = ''):
        instructions = """
                            You are a helpful assistant, which can answer queries on products in stock.
                            ## Instructions:
                            # - Always use the provided tools to answer questions.
                            # - provide well structured output, use lists, bullet point and tables as required.  
                        """
        agent = Agent(
            name = "Movie and Stock Product Information Agent", 
            description = "Perform search on Movie and Stock Product databases to retrieve related in", 
            model = self.model, 
            tools = self.tools, 
            markdown = True, 
            instructions = [instructions], 
            db = SqliteDb(
                session_table = "agent_sessions", 
                db_file = f"{path}agno_sessions/agno_agent_storage.db"
            ), 
            add_history_to_context = True, 
            read_chat_history = True, 
            num_history_runs = 3 
        )
        return agent
    
    async def invoke(self, query, context_id) -> dict[str, Any]:
        print(query)
        response: RunOutput = await self.agent.arun(query, session_id = context_id)
        message = response.messages[-1].content
        pprint(response)
        status = response.status
        print(message, status)

        return {
            "is_task_complete": True, 
            "content": message,
        }
    
    @staticmethod
    async def get_mcp_tools():
        mcp_tools = MCPTools(
            url="http://127.0.0.1:8007/mcpserver", 
            transport='streamable-http'
        )

        await mcp_tools.connect()
        return mcp_tools
    
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

async def main():
    mcp_tools = None
    try:
        mcp_tools = await McpAgent.get_mcp_tools()
        agent = McpAgent([mcp_tools], "./")
        response = await agent.invoke("comedy movies in 2025?", uuid4().hex)
        pprint(response)
    finally:
        if mcp_tools:
            await mcp_tools.close()
    
if __name__ == "__main__":
    asyncio.run(main())