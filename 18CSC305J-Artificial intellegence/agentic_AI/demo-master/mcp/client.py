#!/usr/bin/env python3
"""Simple MCP Client - HTTP/SSE version"""

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    """Main client function"""
    print("=" * 60)
    print("🔌 Client: Connecting to MCP server at http://localhost:8000")
    print("=" * 60)
    
    async with sse_client(url="http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            print("✅ Client: Connected to MCP server!")
            print("-" * 60)
            
            # List available tools
            print("📋 Client: Requesting list of tools...")
            tools = await session.list_tools()
            print(f"\n✨ Available tools: {len(tools.tools)}")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            print("\n" + "-" * 60)
            print("🔧 Client: Calling tool: add_numbers with a=5, b=3")
            print("-" * 60)
            
            # Call the add_numbers tool
            result = await session.call_tool("add_numbers", arguments={"a": 5, "b": 3})
            
            print(f"\n📤 Result received:")
            for content in result.content:
                if hasattr(content, 'text'):
                    print(f"  ✅ {content.text}")
            
            print("\n" + "-" * 60)
            print("🔧 Client: Calling tool: add_numbers with a=10.5, b=20.3")
            print("-" * 60)
            
            # Call with different numbers
            result = await session.call_tool("add_numbers", arguments={"a": 10.5, "b": 20.3})
            
            print(f"\n📤 Result received:")
            for content in result.content:
                if hasattr(content, 'text'):
                    print(f"  ✅ {content.text}")
            
            print("\n" + "=" * 60)
            print("🎉 Client: Execution completed successfully!")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
