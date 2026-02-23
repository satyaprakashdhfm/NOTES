import json
import pandas as pd
import numpy as np
from mcp.server.fastmcp import FastMCP, Context as mcpContext
from pathlib import Path
from mcp.server.fastmcp.resources import TextResource, FileResource, BinaryResource, DirectoryResource
import aiofiles
import asyncio 
from mcp.types import PromptMessage, TextContent
from mcp.server.session import ServerSession
from fastmcp.prompts.prompt import Message
from pydantic import Field
from mcp.types import ModelPreferences
from fastmcp import Context
import pandas as pd
from typing import Annotated
from typing import TypedDict

#---- For STDIO Transport-------
#mcp = FastMCP(name="MCPServer")

#---- For Streamable HTTP Transport-------
mcp = FastMCP(name="MCPServer",  
              port=8007, 
              stateless_http=False, 
              streamable_http_path="/mcpserver", 
              host="127.0.0.1",
              warn_on_duplicate_resources=True)

##  ------- Resource, Tools and prompt Definitions goes here -----------

# RESOURCES=======================================================================================
# 1. Basic Direct / Static resource returning a predefined text
@mcp.resource(uri="resource://greeting",
              name="get_greeting",
              title="Get Greeting message",
              description="Get Simple Greeting message",
              mime_type="text/plain")
async def get_greeting() -> str:
    """Provides a simple greeting message."""
    return "Hello from FastMCP Resources!"

# 2. Exposing simple, predefined text using TextResource Class
notice_resource = TextResource(
    uri="resource://notice",
    title="Application Notice",
    name="Important Notice",
    text='''System maintenance scheduled for Sunday 10th August, 2025, from 10:00 Hrs to 17:00 hrs." \
    During this period, the application will be unavailable. We apologize for any inconvenience this may cause and appreciate your patience as we work to improve our services.'''
)
mcp.add_resource(notice_resource)

# 3. Exposing a static file directly as Resource
log_file_path = Path("app/logs/application.log")
@mcp.resource(uri=f"file://{log_file_path.as_posix()}",
              name="read_application_log",
              title="Read Application Logs",
              description="Read Inventory Management System Log file",
              mime_type="text/plain")
async def read_application_log() -> str:
    """Reads content from a specific log file asynchronously."""
    try:
        async with aiofiles.open(log_file_path, mode="r") as f:
            content = await f.read()
        return content
    except FileNotFoundError:
        return "Log file not found."

# 4. Direct / Static Resource returning JSON data (dict is auto-serialized)
## Helper Function
def read_json_file(file_path):
    """
    Reads a JSON file, parses it, and returns the data as a Python dictionary.
    Args:
        file_path (str): The path to the JSON file.
    Returns:
        dict or None: The parsed JSON data if successful, otherwise None.
    """
    try:
        # Use 'with' statement for safe file handling.
        # It automatically closes the file even if errors occur.
        with open(file_path, 'r') as file:
            # json.load() reads from a file object and parses the JSON.
            data = json.load(file)
            print(f"Successfully read JSON from '{file_path}'")
            return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' contains invalid JSON.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Resource
@mcp.resource(uri="data://config",
              name="get_config",
              title="Get Application Configuration",
              description="Get Inventory Management System Configuration in JSON format",
              mime_type="application/json")
async def get_config() -> dict:
    """Reads application configuration as JSON."""
    file_name = 'data/config.json'
    json_data = read_json_file(file_name)
    return json_data

# 5. Exposing a static file directly using FileResource Class
readme_path = Path("data/README.txt").resolve()
if readme_path.exists():
    # Use a file:// URI scheme
    readme_resource = FileResource(
        uri=f"file://{readme_path.as_posix()}",
        path=readme_path, # Path to the actual file
        name="Project README File",
        description="MC-Hilton Inventory Management System README File.",
        mime_type="text/markdown"
    )
    mcp.add_resource(readme_resource)

# 6. Exposing a directory listing
data_dir_path = Path("data/").resolve()
if data_dir_path.is_dir():
    data_listing_resource = DirectoryResource(
        uri="resource://data-files",
        path=data_dir_path, # Path to the directory
        name="Resource Server Directory Listing",
        description="Lists files available in the Server directory.",
        recursive=True # Set to True to list subdirectories
    )
    mcp.add_resource(data_listing_resource) # Returns JSON list of files

# TOOLS=======================================================================================
# Adding Calculator tools
#Tool returns both Text Content and Structured Output
@mcp.tool(
            name = "add",
            title = "add",
            description = "Add two numbers",
            annotations={
                            'readOnlyHint': True,
                            'destructiveHint': False,
                            'idempotentHint': False,
                            'openWorldHint': False
                        })
async def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool(
            name = "subtract",
            title = "subtract",
            description = "Subtract two numbers",
            annotations={
                            'readOnlyHint': True,
                            'destructiveHint': False,
                            'idempotentHint': False,
                            'openWorldHint': False
                        })
async def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b

@mcp.tool(
            name = "multiply",
            title = "multiply",
            description = "Multiply two numbers",
            annotations={
                            'readOnlyHint': True,
                            'destructiveHint': False,
                            'idempotentHint': False,
                            'openWorldHint': False
                        })
async def multiply(a: int, b: int) -> int:
    """multiply two numbers"""
    return a * b

@mcp.tool(
            name = "divide",
            title = "divide",
            description = "Divide two numbers",
            annotations={
                            'readOnlyHint': True,
                            'destructiveHint': False,
                            'idempotentHint': False,
                            'openWorldHint': False
                        })
async def divide(a: int, b: int) -> int:
    """divide two numbers"""
    if b == 0:
        b = 1
    return a / b

@mcp.tool(
            name = "power",
            title = "power",
            description = "raising to the power",
            annotations={
                            'readOnlyHint': True,
                            'destructiveHint': False,
                            'idempotentHint': False,
                            'openWorldHint': False
                        }
)
async def power(a: int, b: int) -> int:
    """raising to the power"""
    return a ** b

@mcp.tool(
            name = "exponentiate",
            title = "exponentiate",
            description = "raising e to the power",
            annotations={
                            'readOnlyHint': True,
                            'destructiveHint': False,
                            'idempotentHint': False,
                            'openWorldHint': False
                        }
)
async def exponentiate(a: int) -> float:
    """raising e to the power"""
    return np.exp(a)

@mcp.tool(
            name = "natural_logarithm",
            title = "natural logarithm",
            description = "compute natural logarithm",
            annotations={
                            'readOnlyHint': True,
                            'destructiveHint': False,
                            'idempotentHint': False,
                            'openWorldHint': False
                        }
)
async def natural_logarithm(a: float) -> float:
    """raising e to the power"""
    return np.log(a)

@mcp.tool(
        name="get_product",
        description="Retrieve products of a specific category",
        title="Get Product of a Category",
)
async def get_product(query: str, ctx: Context) -> str | list[dict]:
    """Identify the Category of Product discussed in a Query using the client's LLM."""
    df = pd.read_csv("csvs/product.csv")
    categories = str(set(df['Category']))
    prompt = f"""Identify the product category of the following query as {categories}.
    Just output a single word - {categories}.
    Query to analyze: {query}"""
    # Request LLM analysis through sampling
    category = await ctx.sample(messages=prompt,
                                temperature=0.7, 
                                model_preferences=ModelPreferences(
                                    hints=["qwen","claude","gemini"],
                                    costPriority=0.3,
                                    speedPriority=0.8,
                                    intelligencePriority=0.7
                                )
                                )
    print(category.text)
    if category.text in categories:
        response = df[df['Category'] == category.text].to_dict(orient='records')
    else:
        response = "No Data Found!"
    return response

def fetch_users(dataframe, city=None, gender=None):
    """
    Fetches users from the DataFrame based on city, gender, or both.
    Args:
        dataframe (pd.DataFrame): The input DataFrame.
        city (str, optional): The city to filter by. Defaults to None.
        gender (str, optional): The gender to filter by. Defaults to None.
    Returns:
        pd.DataFrame: A DataFrame containing the filtered users.
    """
    query_conditions = pd.Series([True] * len(dataframe)) # Start with all True
    if city:
        query_conditions = query_conditions & (dataframe['City'].str.lower() == city.lower())
    if gender:
        query_conditions = query_conditions & (dataframe['Gender'].str.lower() == gender.lower())
    return dataframe[query_conditions].to_dict(orient='records')

#Tool return Text Content as well as Structured Output as JSON
@mcp.tool(
            name = "search_user",
            title = "search user",
            description = "search user by gender and city",
            annotations={
                            'readOnlyHint': True,
                            'destructiveHint': False,
                            'idempotentHint': True,
                            'openWorldHint': False
                        })
async def search_user(gender: Annotated[str, "gender of user"] | None,
                        city: Annotated[str, "city of user"] | None) -> list[dict]:
    """Search user by gender and city."""
    df = pd.read_csv("csvs/users.csv")
    if gender and city:
        result = fetch_users(df, gender=gender, city=city)
    elif gender:
        result = fetch_users(df, gender=gender)
    elif city:
        result = fetch_users(df, city=city)
    return result

@mcp.tool(
            name = "calculate_average",
            title = "calculate average",
            description = "calculate average of age or salary",
            annotations={
                            'readOnlyHint': True,
                            'destructiveHint': False,
                            'idempotentHint': False,
                            'openWorldHint': False
                        })
async def calculate_average(data: Annotated[list[int] | list[float], "list of numbers"]) -> float:
    """calculate average of numbers"""
    result = 0.0
    if data:
        arr= np.array(data)
        result = np.mean(arr)
    return result

# Using TypedDict for simpler structured output - content
class ServerInfo(TypedDict):
    name: str
    instructions: str | None
    debug_mode: bool
    log_level: str
    host: str
    port: int

"""Tool that uses context capabilities."""
#Tool returns both Text Content and Structured Output as TypedDict
@mcp.tool(  
            name = "server_info",
            title = "server information",
            description = "Get MCP Server information")
async def server_info(ctx: mcpContext[ServerSession, None]) -> ServerInfo:
    """Get information about the current server. Returns structured data"""
    #print(ctx)
    result = ServerInfo(
        name = ctx.fastmcp.name,
        instructions = ctx.fastmcp.instructions,
        debug_mode = ctx.fastmcp.settings.debug,
        log_level = ctx.fastmcp.settings.log_level,
        host = ctx.fastmcp.settings.host,
        port = ctx.fastmcp.settings.port,
    )
    return result

# PROMPTS=======================================================================================
# 1. Basic prompt with simple arguments returning a string (converted to user message automatically) and Decorator Arguments
@mcp.prompt(name="explain-topic",         # Custom prompt name
            title="Prompt Template for explanation",   # Custom description
            description="Generates a user message asking for an explanation of a topic."
            )
def explain_topic(topic: str) -> str:
    """Generates a user message asking for an explanation of a topic. 
    This docstring is ignored when description is provided."""
    return f"Can you please explain the concept of '{topic}'?"

# 2. Basic prompt with structured arguments returning a string (converted to user message automatically) and Decorator Arguments
@mcp.prompt(
    name="summarize_prompt",
    description="Creates a request to summarize a content with specific parameters",
)
def summarize_prompt(
    content_uri: str = Field(description="The URI of the resource containing the content."),
    summary_type: str = Field(default="short", description="Type of summary.")
) -> str:
    """This docstring is ignored when description is provided."""
    return f"Please perform a '{summary_type}' summary on the text found at {content_uri}."

# Return Values
# 3. Prompt returning a specific message type - Example of Inferred Metadata (name=function name, description=docstring)
@mcp.prompt()
def generate_code_request(language: str, task_description: str) -> PromptMessage:
    """Generates a user message requesting code generation."""
    content = f"Write a {language} function that performs the following task: {task_description}"
    return PromptMessage(role="user", content=TextContent(type="text", text=content))

# 4. Prompt returning a list of prompt messages - Example of Inferred Metadata (name=function name, description=docstring)
@mcp.prompt()
def roleplay_scenario(character: str, situation: str) -> list[PromptMessage]:
    """Sets up a roleplaying scenario with initial messages."""
    return [
        Message(f"Let's roleplay. You are {character}. The situation is: {situation}"),
        Message("Okay, I understand. I am ready. What happens next?", role="assistant")
    ]

# 5. Prompt with Required vs. Optional Parameters
@mcp.prompt()
def data_analysis_prompt(
    data_uri: str,                        # Required - no default value
    analysis_type: str = "short",       # Optional - has default value
    include_charts: bool = False          # Optional - has default value
) -> str:
    """Creates a request to analyze data with specific parameters."""
    prompt = f"Please perform a '{analysis_type}' analysis on the data found at {data_uri}."
    if include_charts:
        prompt += " Include relevant charts and visualizations."
    return prompt

def main():
    """Entry point for the direct execution server."""
    mcp.run(
            #transport="stdio" #For STDIO Transport
            transport="streamable-http"
            )
    
if __name__ == "__main__":
    main()