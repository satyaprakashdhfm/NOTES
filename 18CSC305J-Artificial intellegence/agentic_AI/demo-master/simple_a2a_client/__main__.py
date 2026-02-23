import logging
from typing import Any
from uuid import uuid4
from rich.pretty import pprint
import httpx
from a2a.client import (
        A2ACardResolver, 
        A2AClient, 
        A2ACardResolver
    )
from a2a.utils.message import get_message_text
from a2a.types import TransportProtocol
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
)
import warnings
warnings.filterwarnings("ignore")
def get_user_query() -> str:
    return input('\n> ')
    
def print_initwelcome_message() -> None:
    print("\n\n")
    print('==================================Welcome to the A2A client!======================================')
    print("Example: Communicating with a Remote A2A Server")
    print("==================================================================================================")
    print("Please enter your query (type 'exit' to quit):\n")
async def main() -> None:
    # Configure logging to show INFO level messages
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)  # Get a logger instance
    # URL of the Remote Agent hosted via A2A Protocol Server 
    base_url = 'http://127.0.0.1:8024'
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        
        # Fetch Public Agent Card and Initialize Client
        agent_card: AgentCard | None = None
        logger.info(
            f'Attempting to fetch public agent card from: {base_url}{AGENT_CARD_WELL_KNOWN_PATH}'
        )
        try:
            agent_card = (
                await resolver.get_agent_card()
            )  # Fetches from default public path
            logger.info('Successfully fetched public agent card')
            pprint(agent_card)
            
            logger.info(
                '\nUsing PUBLIC agent card for client initialization (default).'
            )
        except Exception as e:
            logger.error(f'Critical error fetching public agent card: {e}', exc_info=True)
            raise RuntimeError('Failed to fetch the public agent card. Cannot continue.') from e
        client = A2AClient(httpx_client=httpx_client, 
                           agent_card=agent_card
                        )
        logger.info('A2AClient initialized.')
        print_initwelcome_message()
        while True:
            user_input = get_user_query()
            if user_input.lower() == 'exit':
                print('bye!~')
                break
            try:
                # Create the message object
                send_message_payload: dict[str, Any] = {
                    'message': {
                        'role': 'user',
                        'parts': [
                            {'kind': 'text', 'text': user_input}
                        ],
                        'messageId': uuid4().hex,
                    },
                }
                
                # Send the message to the A2A server
                request = SendMessageRequest(
                    id=str(uuid4()), params=MessageSendParams(**send_message_payload)
                )
                response = await client.send_message(request)
                # Check if response has root
                if not hasattr(response, 'root') or not response.root:
                    logger.error("Response missing 'root' attribute")
                    return "Error: Invalid response format from A2A server"
                    
                # Check if root is an error response
                if hasattr(response.root, 'error') and response.root.error:
                    logger.error(f"A2A server error: {response.root.error}")
                    return f"A2A Server Error: {response.root.error}"
                    
                # Check if root has result (success response)
                if not hasattr(response.root, 'result') or not response.root.result:
                    logger.error("Response missing 'result' attribute")
                    return "Error: Invalid response format from A2A server"
                
                # Extract response data
                result = response.root.result
                pprint(result)
                
                # Get the response content from artifacts
                # Check if Result has Artifact(s)
                # If Result has multiple Artifacts
                if hasattr(result, 'artifacts') and result.artifacts:
                    # Extract content from the first artifact
                    artifact = result.artifacts[0]
                # If Result has a Single Artifact
                elif hasattr(result, 'artifact') and result.artifact:
                    # Extract content from the only artifact available
                    artifact = result.artifact
                # Fallback: check for content in other locations
                elif hasattr(result, 'content') and result.content:
                    logger.info(f"Successfully retrieved response from A2A server")
                    content = result.content
                    print("Ans:", content,"\n")
                else:
                    logger.warning("No content found in A2A server response")
                    print("No response content received from A2A server")
                # When Artifact Exists then Retrieve the Text Content from the Root object of its Part
                if artifact:
                	# Checks if Artifact has Part object
                    if hasattr(artifact, 'parts') and artifact.parts:
                        part = artifact.parts[0]
                        # Checks if Part has Root object and Root has text
                        if hasattr(part, 'root') and hasattr(part.root, 'text'):
                            content = part.root.text
                            logger.info(f"Successfully retrieved response from A2A server")
                            print("Ans:", content,"\n")
            except Exception as e:
                logger.error(f"Error communicating with A2A server: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                print(f"Error communicating with A2A server: {str(e)}")
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
