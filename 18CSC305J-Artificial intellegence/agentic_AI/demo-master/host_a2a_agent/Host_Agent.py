from rich.pretty import pprint
import asyncio, json, os, uuid, logging, httpx
from dotenv import load_dotenv
from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard, 
    Task, 
    MessageSendParams, 
    SendMessageRequest, 
    SendMessageResponse, 
    SendMessageSuccessResponse, 
)
from google.adk import Agent 
from google.adk.agents.callback_context import CallbackContext, ReadonlyContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from .remote_agent_connection import RemoteAgentConnections, TaskUpdateCallback

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def read_json_as_dict(filename : str)->dict : 
    """ reads a json file and returns its cnotent as python dictionary"""
    try:
        with open(filename,'r') as file :
            data_dict = json.load(file)
            return data_dict
    except FileNotFoundError:
        print("error the file was not found")
        return None
    except json.JSONDecodeError:
        print("error the file cant be decoded to dict")
        return None


def llm():
    """Initialize AWS Bedrock Nova Lite model via LiteLLM for the host agent."""
    bedrock_llm = LiteLlm(
        model="bedrock/amazon.nova-lite-v1:0",
        temperature=0.7,
        aws_region_name="us-east-1"
    )
    return bedrock_llm

class HostAgent:
    def __init__(
            self, 
            task_callback: TaskUpdateCallback | None = None,
    ):
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ''
    
    async def _async_init_components(
            self, remote_agent_addresses: list[str]
    ) -> None:
        async with httpx.AsyncClient(timeout=300) as httpx_client:
            for address in remote_agent_addresses:
                card_resolver = A2ACardResolver(
                    httpx_client = httpx_client, 
                    base_url = address, 
                )
                try:
                    card = (
                        await card_resolver.get_agent_card()
                    )

                    remote_connection = RemoteAgentConnections(
                        agent_card = card, agent_url = address
                    )

                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card
                except httpx.ConnectError as e:
                    logger.debug(
                        'ERROR: Failed to get agent card from %s: %s', 
                        address, 
                        e
                    )
        for agent_name,card in self.cards.items():
            print(agent_name)
            pprint(card)
        agent_info = []
        for agent_detail_dict in self.list_remote_agents():
            agent_info.append(json.dumps(agent_detail_dict))
        self.agents = '\n'.join(agent_info)

    
    def list_remote_agents(self):
        if not self.remote_agent_connections:
            return []
        else:
            remote_agent_info = []
            for card in self.cards.values():
                logger.info(
                    "Found agent card: %s", card.model_dump(exclude_none=True)
                )
                logger.info("=" * 100)
                remote_agent_info.append(
                    {"name": card.name, 'description': card.description}
                )
            return remote_agent_info
    
    @classmethod
    async def create(
        cls,
        task_callback: TaskUpdateCallback | None = None, 
    ) -> 'HostAgent':
        instance = HostAgent(task_callback)
        
        LANGGRAPH_AGENT = os.getenv('LANGGRAPH_AGENT')
        remote_agent_addresses = [LANGGRAPH_AGENT]
        await instance._async_init_components(remote_agent_addresses)
        return instance

    def create_agent(self) -> Agent:
        return Agent(
            model = llm(), 
            name = "host_agent", 
            instruction = self.root_instruction, 
            before_model_callback = self.before_model_callback, 
            description = (
                "This agent orchestrates the decomposition of the user request into"
            ), 
            tools = [
                self.list_remote_agents, 
                self.send_message,
            ], 
        )
    
    def check_active_agent(self, context: ReadonlyContext):
        state = context.state
        if (
            "session_id" in state 
            and "session_active" in state 
            and state['session_active']
            and 'agent' in state
        ):
            return {"active_agent": f"{state['active_agent']}"}
        return {'active_agent': "None"}
    
    def before_model_callback(
            self, callback_context: CallbackContext, llm_request
    ):
        state = callback_context.state
        if 'session_active' not in state or not state['session_active']:
            if 'session_id' not in state:
                state['session_id'] = str(uuid.uuid4())
            state['session_active'] = True

    async def send_message(
            self, agent_name: str, message: str, tool_context: ToolContext
    ):
        """
    **Current Active agent:** {current_agent['active_agent']}

    Send msg doc string: 
    Sends a task either streaming (if supported) or non-streaming.

       This will send a message to the remote agent named agent_name.

       Args:
         agent_name: The name of the agent to send the task to.
         message: The message to send to the agent for the task.
         tool_context: The tool context this method runs in.

       Yields:
         A dictionary of JSON data.
    """
        if agent_name == "host_agent":
            raise ValueError("host_agent cannot send messages to itself")

        if agent_name not in self.remote_agent_connections:
            raise ValueError(f"Agent {agent_name} not found. {message}")
        
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f"Agent {agent_name} not found. {message}")
        state = tool_context.state
        state['active_agent'] = agent_name
        client = self.remote_agent_connections[agent_name]

        if not client:
            raise ValueError(f"Client not available for {agent_name}")
        task_id = state.get('task_id', None)
        context_id = state.get('context_id', None)
        message_id = ''
        metadata = {}

        if 'input_message_metadata' in state:
            metadata.update(**state['input_message_metadata'])
            if 'message_id' in state['input_message_metadata']:
                message_id = state['input_message_metadata']['message_id']
        
        if not message_id:
            message_id = str(uuid.uuid4())
        
        payload = {
            'message': {
                'role': 'user', 
                'parts': [
                    {'kind': 'text', 'text': message}
                ], 
                'messageId': message_id
            }, 
        }

        if task_id:
            payload['message']['taskId'] = task_id
        
        if context_id:
            payload['message']['contextId'] = context_id
        
        message_request = SendMessageRequest(
            id = message_id, params = MessageSendParams.model_validate(payload)
        )

        send_response: SendMessageResponse = await client.send_message(
            message_request = message_request
        )

        logger.info(
            'send_response', 
            send_response.model_dump_json(exclude_none=True, indent=4)
        )

        if not isinstance(send_response.root, SendMessageSuccessResponse):
            logger.info("Received non_success response, aborting get task")
            return None
        
        if not isinstance(send_response.root.result, Task):
            logger.info("Received non-task response, aborting ")
            return None
        
        result = send_response.root.result

        if hasattr(result, 'artifacts') and result.artifacts:
            artifact = result.artifacts[0]
        elif hasattr(result, 'artifact') and result.artifact:
            artifact = result.artifact
        elif hasattr(result, 'content') and result.content:
            logger.info(f"Successfully retrieved response from A2A server")
            content = result.content
            return content
        else:
            logger.warning("No content")
            print("No response")
            return None
        
        if artifact:
            if hasattr(artifact, 'parts') and artifact.parts:
                part = artifact.parts[0]
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    content = part.root.text
                    logger.info(f"Successfully retrived response from A2A server")
                    return content

        return None

    def root_instruction(self, context: ReadonlyContext) -> str:
       """Generate the root instruction for the HostAgent."""
       current_agent = self.check_active_agent(context)
       return f"""
    **Role:** You are an expert delegator that can delegate the user request to the appropriate specialized remote agents.
    Discovery:
    - You can use `list_remote_agents` to list the available remote agents you can use to delegate the task.

    **Task Delegation:**
    - For actionable requests, you can use `send_message` to interact with remote agents to take action, to assign actionable tasks to remote agents..

    Be sure to include the remote agent name when you respond to the user.
    Important:
    # **Tool Reliance:** If the user input is conversational (greetings, acknowledgements, clarifications),
    respond directly without using any tool.

    Use tools ONLY when delegation to a remote agent is required.
    # If you are not sure, please ask the user for more details.
    # **Prioritize Recent Interaction:** Focus on the most recent parts of the conversation primarily when processing requests.
    # **No Redundant Confirmations:** Do not ask remote agents for confirmation of information or actions.
    # **Focused Information Sharing:** Provide remote agents with only relevant contextual information. Avoid extraneous details.
    # **Transparent Communication:** Always present the complete and detailed response from the remote agent to the user.
    # **Autonomous Agent Engagement:** Never seek user permission before engaging with remote agents. If multiple agents are required to fulfill a request, connect with them directly without requesting user preference or confirmation.

    **Available Agents:**
    {self.agents}
    """




