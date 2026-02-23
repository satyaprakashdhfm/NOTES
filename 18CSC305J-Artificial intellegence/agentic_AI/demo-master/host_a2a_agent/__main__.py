import asyncio
# import gradio as gr  # Not needed for CLI version
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from .Host_Agent import HostAgent
from collections.abc import AsyncIterator
from google.adk import Agent
from pprint import pformat
from uuid import uuid4
import traceback
from rich.pretty import pprint

APP_NAME = "simpleA2A_app"
USER_ID = "default_user"
SESSION_ID = uuid4().hex

def get_agent() -> Agent:
    async def get_host_agent() -> Agent:
        routing_agent_instance = await HostAgent.create()
        return routing_agent_instance.create_agent()
    try:
        return asyncio.run(get_host_agent())
    except RuntimeError as e:
        if 'asyncio.run() cannot be called from a running event loop' in str(e):
            print(
                f"Warning: {e}"
            )
    raise

SESSION_SERVICE = InMemorySessionService()
ROUTING_AGENT_RUNNER = Runner(
    agent = get_agent(), 
    app_name = APP_NAME, 
    session_service = SESSION_SERVICE
)

async def get_response_from_agent(
    message: str, 
    # history: list[gr.ChatMessage], 
) -> str:
# AsyncIterator[gr.ChatMessage]:
    try:
        event_iterator: AsyncIterator[Event] = ROUTING_AGENT_RUNNER.run_async(
            user_id = USER_ID, 
            session_id = SESSION_ID, 
            new_message = types.Content(
                role = "user", parts = [types.Part(text=message)]
            ), 
        )

        print("Events:", "-" * 30)
        async for event in event_iterator:
            if event.content and event.content.parts:
                print("Event Content: ", end = "")
                pprint(event.content)
                for part in event.content.parts:
                    if part.function_call:
                        formatted_call = f'```python\n{pformat(part.function_call.model_dump(exclude_none=True), indent=2, width=80)}\n```'
                        pprint(
                            {
                                "role": "assistant", 
                                "content": f" **Tool Call: {part.function_call.name}**\n{formatted_call}"
                            }
                        )
                    elif part.function_response:
                        response_content = part.function_response.response
                        if (isinstance(response_content, dict) and 'response' in response_content):
                            formatted_response_data = response_content['response']
                        else:
                            formatted_response_data = response_content
                        formatted_response = f'```json\n{pformat(formatted_response_data, indent=2, width=80)}\n```'
                        pprint(
                            {
                                "role": "assistant", 
                                "content": f'**Tool Response from {part.function_response.name}**\n{formatted_response}'
                            }
                        )
                
            if event.is_final_response():
                final_response_text = ''
                if event.content and event.content.parts:
                    final_response_text = ''.join([p.text for p in event.content.parts if p.text])
                elif event.actions and event.actions.escalate:
                    final_response_text = f'Agent escalated: {event.error_message or "No specific message."}'
                if final_response_text:
                    pprint({"role": 'assistant', 'content': final_response_text})
                    return final_response_text
                break

    except Exception as e:
        print(f'Error in get_response_from_agent (Type: {type(e)}): {e}')
        return 'an error occured while processing your request. Please check the server logs for details.'
    
async def main():
    print("Creating ADK session...")
    await SESSION_SERVICE.create_session(
        app_name = APP_NAME, user_id = USER_ID, session_id = SESSION_ID
    )
    print("ADK session created successfully.")

    while True:
        print("\n\n")
        print("Please enter your query (type 'exit' to quit):")
        user_input = input()

        if user_input.lower() == 'exit':
            print("Bye!=")
            break
        else:
            resp = await get_response_from_agent(user_input)
            print("AI:", resp)

if __name__ == '__main__':
    asyncio.run(main())