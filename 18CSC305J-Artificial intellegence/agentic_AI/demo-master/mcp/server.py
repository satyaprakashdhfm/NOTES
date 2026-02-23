#!/usr/bin/env python3
"""Simple MCP Server with one tool - HTTP/SSE version"""

import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn


# Create server instance
app = Server("simple-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    print("📋 Server: Listing available tools...")
    return [
        Tool(
            name="add_numbers",
            description="Add two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["a", "b"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    print(f"🔧 Server: Tool called - {name}")
    print(f"   Arguments: {arguments}")
    
    if name == "add_numbers":
        a = arguments.get("a")
        b = arguments.get("b")
        result = a + b
        print(f"   ✅ Result: {result}")
        return [
            TextContent(
                type="text",
                text=f"The sum of {a} and {b} is {result}"
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")


# Create SSE transport
sse = SseServerTransport("/messages")


async def handle_sse(request):
    """Handle SSE connections"""
    print("🔌 Server: New client connected!")
    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send,
    ) as streams:
        print("✅ Server: Client connection established")
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options(),
        )
    print("👋 Server: Client disconnected")


async def handle_messages(request):
    """Handle POST messages"""
    print("📨 Server: Received message from client")
    return await sse.handle_post_message(request.scope, request.receive, request._send)


# Create Starlette app
starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ],
)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting MCP Server on http://localhost:8000")
    print("=" * 60)
    print("📡 SSE endpoint: http://localhost:8000/sse")
    print("📬 Messages endpoint: http://localhost:8000/messages")
    print("=" * 60)
    uvicorn.run(starlette_app, host="0.0.0.0", port=8000)
