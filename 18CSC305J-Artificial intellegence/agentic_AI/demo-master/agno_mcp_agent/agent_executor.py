from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.utils import new_task
import logging
from a2a.types import (
    InternalError,
    InvalidRequestError,
    Part,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from .mcp_agent import McpAgent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPAgentExecutor(AgentExecutor):
    """Websearch Remote Agent Implementation."""
    def __init__(self):
        self.agent = None
        self.mcp_tools = None
        
    async def _init_agent(self):
        if self.agent is None:
            self.mcp_tools = await McpAgent.get_mcp_tools()
            self.agent = McpAgent([self.mcp_tools], "./agno_mcp_agent/")
            
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        await self._init_agent()
        # Checking if Context Exists ------------------------------------------
        if not context:
            raise ServerError(error=InvalidRequestError())
        
        # Getting the Message (query) sent from the A2A Client ----------------
        query = context.get_user_input()
        
        task = context.current_task
        print("="*20,"Context Information","="*30)
        print("Context Id:",context.context_id)
        print("query:",query)
        print("Task Id:",context.task_id)
        print("Context Task:",task)
        print("Context Message:",context.message)
        print("-"*70)
        # Creating a New Task if Task does not exists. And adding the same to the event queue.
        if not task:
            task = new_task(context.message)  # type: ignore
            await event_queue.enqueue_event(task)
        # Creating the Task Updater for the Current Task (Task Id) and Context (Context Id)---------
        # - Which adds the Task Updates (Status or concrete Artifacts - responses) to the Event Queue
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        # Invoking the Agent with the received query -----------------------------
        try:
            # Inform that the task is in working state
            await updater.start_work()

            # Stream response from the agent and publish chunked artifacts
            first = True
            artifact_id = None
            async for chunk in self.agent.stream(query, task.context_id):
                # Each chunk is expected to be a dict with 'text' and 'is_last'
                text = chunk.get('text', '')
                last = bool(chunk.get('is_last', False))

                # Build a Part with the text chunk
                part = Part(root=TextPart(text=text))

                # For streaming, use append=True for intermediate chunks and last_chunk flag
                await updater.add_artifact(
                    parts=[part],
                    artifact_id=artifact_id,
                    name='websearch_result',
                    append=not first,
                    last_chunk=last,
                )
                first = False
                # After first add, subsequent adds should reuse same artifact id - TaskUpdater will generate id when None
                if last:
                    # mark completion
                    await updater.complete()
                    break

        except Exception as e:
            logger.error(f'An error occurred while getting the response: {e}')
            # publish failed state
            await updater.failed()
            raise ServerError(error=InternalError()) from e
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise ServerError(error=UnsupportedOperationError())