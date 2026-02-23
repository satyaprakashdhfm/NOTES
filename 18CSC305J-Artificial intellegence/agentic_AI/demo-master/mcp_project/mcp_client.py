import asyncio
import os
from tabulate import tabulate
from pprint import pprint
import json
from pydantic import AnyUrl
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.context import RequestContext
from mcp.shared.metadata_utils import get_display_name

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="uv",  # Using uv to run the server
    args=["run", "python", "mcp_server.py"],
    env={"UV_INDEX": os.environ.get("UV_INDEX", "")},
)

## ------- Tool, Resource and Prompts usage and Sampling Callback defining Code goes here -----------

async def display_tools(session: ClientSession):
    """Display available tools with human-readable names"""
    tools_response = await session.list_tools()
    for tool in tools_response.tools:
        # get_display_name() returns the title if available, otherwise the name
        display_name = get_display_name(tool)
        print(f"Tool: {display_name}")
        if tool.description:
            print(f"   {tool.description}")

async def display_resources(session: ClientSession):
    """Display available resources with human-readable names"""
    resources_response = await session.list_resources()
    for resource in resources_response.resources:
        display_name = get_display_name(resource)
        print(f"Resource: {display_name} ({resource.uri})")
    templates_response = await session.list_resource_templates()
    for template in templates_response.resourceTemplates:
        display_name = get_display_name(template)
        print(f"Resource Template: {display_name}")

async def display_prompts(session: ClientSession):
    """Display available prompts with human-readable names"""
    prompts_response = await session.list_prompts()
    for prompt in prompts_response.prompts:
        display_name = get_display_name(prompt)
        print(f"Prompt: {display_name}")
        if prompt.description:
            print(f"   {prompt.description}")

## ------- Implementation Code -----------

async def run_stdio():
    """Run the MCP client with STDIO transport"""
    # Connecting to STDIO server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            print("\n=== MCP Server Capabilities ===\n")
            
            # Display available tools
            print("--- Tools ---")
            await display_tools(session)
            
            # Display available resources
            print("\n--- Resources ---")
            await display_resources(session)
            
            # Display available prompts
            print("\n--- Prompts ---")
            await display_prompts(session)

async def run_http():
    """Run the MCP client with Streamable-HTTP transport"""
    # Connecting to Streamable-HTTP server
    async with streamablehttp_client("http://127.0.0.1:8007/mcpserver") as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            print("\n=== MCP Server Capabilities ===\n")
            
            # Display available tools
            print("--- Tools ---")
            await display_tools(session)
            
            # Display available resources
            print("\n--- Resources ---")
            await display_resources(session)
            
            # Display available prompts
            print("\n--- Prompts ---")
            await display_prompts(session)

async def run():
    """Main run function - choose transport type"""
    # Change this to switch between STDIO and HTTP transports
    transport_type = os.environ.get("MCP_TRANSPORT", "stdio")  # "stdio" or "http"
    
    if transport_type == "http":
        await run_http()
    else:
        await run_stdio()

def main():
    """Entry point for the client script."""
    asyncio.run(run())

if __name__ == "__main__":
    main()