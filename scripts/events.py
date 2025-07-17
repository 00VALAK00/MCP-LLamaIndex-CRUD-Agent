from llama_index.core.agent.workflow import ToolCallResult
from llama_index.core.llms import ChatMessage,ChatResponse
from llama_index.core.tools import ToolSelection
from llama_index.core.workflow import Event



class PrepEvent(Event):
    "Event to handle new messages and prepare the chat history"

class LLMInputEvent(Event):
    input: list[ChatMessage]

class LLMOutputEvent(Event):
    output: ChatResponse


class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]


