import asyncio
import logging
from typing import Any
from uuid import uuid4
from rich.pretty import pprint
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendStreamingMessageRequest,
)
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from a2a.utils.message import get_message_text


def get_user_query() -> str:
    return input('\n> ')


def print_initwelcome_message() -> None:
    print('\n\n')
    print('Streaming Example : Understanding A2A server streaming operations')


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    base_url = 'http://127.0.0.1:8024'

    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        try:
            agent_card = await resolver.get_agent_card()
            logger.info('Fetched agent card')
            pprint(agent_card)
        except Exception as e:
            logger.error(f'Failed to fetch agent card: {e}')
            return

        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        print_initwelcome_message()
        while True:
            user_input = get_user_query()
            if user_input.lower() == 'exit':
                print('bye!~')
                break

            send_message_payload: dict[str, Any] = {
                'message': {
                    'role': 'user',
                    'parts': [
                        {'kind': 'text', 'text': user_input}
                    ],
                    'messageId': uuid4().hex,
                },
            }

            request = SendStreamingMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))
            try:
                stream = client.send_message_streaming(request)
                # stream is an async iterator of A2A client events/messages
                async for event in stream:
                    # Print raw event for visibility
                    pprint(event)
                    # The a2a client returns either Message or Task events; try extracting text
                    try:
                        if hasattr(event, 'root') and event.root and hasattr(event.root, 'result') and event.root.result:
                            result = event.root.result
                            # If artifacts present, extract text
                            if hasattr(result, 'artifacts') and result.artifacts:
                                artifact = result.artifacts[0]
                                if hasattr(artifact, 'parts') and artifact.parts:
                                    part = artifact.parts[0]
                                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                        print('\nAns chunk:', part.root.text, '\n')
                            elif hasattr(result, 'content') and result.content:
                                print('\nAns chunk:', result.content, '\n')
                    except Exception:
                        pass

            except Exception as e:
                logger.error(f'Error during streaming request: {e}')


if __name__ == '__main__':
    asyncio.run(main())
