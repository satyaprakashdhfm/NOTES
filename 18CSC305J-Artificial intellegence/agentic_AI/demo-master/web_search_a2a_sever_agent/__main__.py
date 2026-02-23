import sys, httpx, click, logging, uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from .agent_executor import WebSearchAgentExecutor
from .WebSearchAgent import WebsearchAgent
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@click.command()
@click.option('--host', 'host', default='127.0.0.1')
@click.option('--port', 'port', default=8024)
def main(host, port):
    try:
        # Defining Agent Skills, capabilities and Agent Card --------------------------
        capabilities = AgentCapabilities(streaming=True, push_notifications=True)
        skill = AgentSkill(
            id='web_search',
            name='Perform Web search',
            description='perform real-time information retrieval from open internet using google search',
            tags=['search', 'web'],
            examples=['Which tean won Asia Cup in 2025?'],
        )
        agent_card = AgentCard(
            name='Websearch Agent',
            description='Helps with searching and retrieving real-time information on any topic from the open internet using google search',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            default_input_modes=WebsearchAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=WebsearchAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(httpx_client=httpx_client,
                        config_store=push_config_store)
        
        # Creating the Request Handler---------------------------------------------
        request_handler = DefaultRequestHandler(
            agent_executor=WebSearchAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender= push_sender,
        )

        # Creating the A2A Starlette Application with the Agent Card and Request Handler
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )
        # Running the Uvicorn Server ----------------------------------------------
        uvicorn.run(server.build(), host=host, port=port)
       
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        sys.exit(1)
 
if __name__ == '__main__':
    main()
