from langchain_ollama.chat_models import ChatOllama
#from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_aws import ChatBedrockConverse
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import Tool
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import InMemorySaver
from typing import Any, AsyncIterable
import asyncio
from langchain.agents import create_agent
load_dotenv()

llm = ChatBedrockConverse(model="amazon.nova-lite-v1:0", region_name="us-east-1",temperature=0.9)
params = {
    "engine": "google",
    "gl": "in",
    "hl": "en",
    "num": 10,
}
websearch = SerpAPIWrapper(params=params)
class SerpInputs(BaseModel):
    """Inputs to the SerpAPI tool."""
    query: str = Field(
        description="query to look up in open internet"
    )
websearch_tool = Tool(
    name="perform_websearch",
    description="Perform real-time search in the open web using google.",
    func=websearch.run,
    args_schema=SerpInputs,
)
class WebsearchAgent:
    async def stream(self, query, content_id) -> AsyncIterable[dict[str, Any]]:
        """Async generator that streams incremental chunks of the agent response.

        Implementation note: the underlying websearch tool returns a full result
        in this codebase. For a streaming demo we call the synchronous
        invoke() to produce the final content and then yield it in smaller
        chunks so the server and client can exercise streaming behaviour.
        """
        # Produce the complete answer using the existing invoke path.
        # Keep this synchronous invocation to reuse the agent logic.
        result = self.invoke(query, content_id)
        content = result.get('content') or ''

        # Defensive: if no content, yield an empty final chunk
        if not content:
            yield {'text': '', 'is_last': True}
            return

        # Split into chunks (by sentence or by fixed size fallback)
        # Try splitting on sentences first for nicer partial outputs.
        import re
        sentences = re.split(r'(?<=[\.\?!])\s+', content)
        if len(sentences) <= 1:
            # fallback to fixed-size chunks
            chunk_size = 200
            sentences = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]

        # Yield each chunk with a small await to allow cooperative scheduling
        for i, s in enumerate(sentences):
            # Trim and skip empty
            text = s.strip()
            if not text:
                continue
            await asyncio.sleep(0)  # allow event loop to interleave
            yield {'text': text, 'is_last': i == len(sentences) - 1}
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
    SYSTEM_INSTRUCTION = (
            "You are a specialized assistant for for question-answering tasks which search the web to retreive relevant information on a given topic from the open internet. "
            "Your sole purpose is to use the 'perform_websearch' tool to Search the web to retrieve latest relevant information required to answer the given query.\n"
            "Use the retrieved relevant information to answer the question. \n"
            "Summarize over the retrieved contents to formulate a comprehensive answer. \n"
            "Important:\n"
            " - Provide well structured output with section headings. \n"
            " - use lists, tables, and bullet points if required. \n"
            "If you don't know the answer, just say that you don't know. \n"    
    )
    def __init__(self):
        self.model = llm
        self.tools = [websearch_tool]
        self.graph = create_agent(
            self.model,
            tools=self.tools,
            checkpointer=InMemorySaver(),
            system_prompt=self.SYSTEM_INSTRUCTION,
            debug=True
        )
    def invoke(self, query, context_id) -> dict[str, Any]:
        inputs = {'messages': [('user', query)],'status':'submitted'}
        config = {'configurable': {'thread_id': context_id}}
        print(inputs)
        output = self.graph.invoke(inputs,config=config)
        message = output['messages'][-1].content
        return {
                    'is_task_complete': True,
                    'content':message,
                }
