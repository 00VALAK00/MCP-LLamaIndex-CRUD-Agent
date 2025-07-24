import asyncio
from re import S
import sys
import subprocess
from pathlib import Path
from turtle import st

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from llama_index.core.llms import ChatMessage,ChatResponse
from llama_index.llms.ollama import Ollama
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec



from llama_index.core.agent.react import ReActChatFormatter, ReActOutputParser
from llama_index.core.agent.react.types import ActionReasoningStep, ObservationReasoningStep

from llama_index.core.workflow import StartEvent,StopEvent,Workflow,step
from llama_index.core.memory import Memory
from llama_index.core.workflow import Context


from config.prompts import SYSTEM_PROMPT
from config.settings import OllamaConfig
from .events import * 


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class DatabaseWorkflow(Workflow):
    def __init__(self) -> None:
        super().__init__(timeout=120.0)
        self.agent = None
        self.llm = None
        self.mcp_client = None
        self.tools = None
        self.ollama_config = None
        self.memory = Memory.from_defaults()


    async def initialize(self,is_docker: bool):
        """Initialize the MCP server and agent"""
        logger.info("🚀 Initializing MCP server...")

        # Initialize LLM
        self.ollama_config = OllamaConfig.get_config(is_docker)
        self.llm = Ollama(
            model= self.ollama_config["model"],
            base_url= self.ollama_config["base_url"],
            context_window= self.ollama_config["context_window"],
            max_tokens= self.ollama_config["max_tokens"],
            temperature= self.ollama_config["temperature"],
            request_timeout= self.ollama_config["request_timeout"],
        )
        assert self.llm.metadata.is_function_calling_model, "LLM must be a function calling model"

        # Start MCP server
        subprocess.Popen([sys.executable, "mcp/mcp_server.py"])
        await asyncio.sleep(2)  # Give server time to start
        
        # Initialize MCP client and tools
        self.mcp_client = BasicMCPClient("http://127.0.0.1:8000/sse")
        mcp_tools = McpToolSpec(client=self.mcp_client)
        self.tools = await mcp_tools.to_tool_list_async()
        self.tools_dict = {tool.metadata.get_name():tool  for tool in self.tools}

        # Debug: Print available tools
        logger.info(f"🔧 Available tools: {self.tools_dict.keys()}")

        logger.info("✅ Database Workflow initialized successfully!")

    @step
    async def new_user_msg(self, workflow_context : Context, ev : StartEvent) -> PrepEvent:
        user_input = ev.input
        self.memory.put(ChatMessage(role="system", content=SYSTEM_PROMPT))
        self.memory.put(ChatMessage(role="user", content=user_input))  
        await workflow_context.store.set("steps", [])
        return PrepEvent()  

    @step
    async def prepare_llm_prompt(self, workflow_context: Context, ev : PrepEvent) -> LLMInputEvent:
        """Prepares the react prompt, using the chat history, tools, and current reasoning (if any)"""

        steps = await workflow_context.get("steps", default=[])
        chat_history = self.memory.get()

        llm_input = ReActChatFormatter().format(tools=self.tools, chat_history=chat_history, current_reasoning=steps)
        
        return LLMInputEvent(input=llm_input)
    
    @step
    async def invoke_llm(self, ev : LLMInputEvent) -> LLMOutputEvent:
        """Handles the LLM output, including tool calls and final response"""
        llm_output = await self.llm.achat(ev.input)

        return LLMOutputEvent(output=llm_output)         
        
    

    @step        
    async def handle_llm_input(
    self, workflow_context: Context, ev : LLMOutputEvent
    )-> ToolCallEvent | PrepEvent | StopEvent:
        """
        Parse the LLM response to extract any tool calls requested.
        If theere is no tool call, we can stop and emit a StopEvent. Otherwise, we emit a ToolCallEvent to handle tool calls.
        """        
        try:
            step = ReActOutputParser().parse(ev.output.message.content)
            steps = await workflow_context.store.get("steps", default=[])
            steps.append(step)

            if step.is_done:
                # final step of the reasoning process
                return StopEvent(result=step.response)
            elif isinstance(step, ActionReasoningStep):
                # Tool call are requested by the LLM
                logger.info(f"🔍 Action: {step.thought}")
                logger.info(f"🔍 Action inputs: {step.action_input}")
                logger.info(f"🔍 Tool call requested: {step.action}")
                return ToolCallEvent(tool_calls=[ToolSelection(
                                                tool_id="Tool_ID",
                                                tool_name=step.action, 
                                                tool_kwargs=step.action_input)
                                                ])
            elif isinstance(step, ObservationReasoningStep):
                # No tool call are requested by the LLM
                logger.info(f"🔍 Observation: {step.observation}")
            
        except Exception as e:
            error_step = ObservationReasoningStep(observation=f"Error parsing LLM output: {e}")
            steps = await workflow_context.store.get("steps", default=[])
            steps.append(error_step)
        
        return PrepEvent()

    @step
    async def handle_tool_calls(
        self, ctx: Context, ev: ToolCallEvent
    ) -> PrepEvent:
        tool_calls = ev.tool_calls


        for tool_call in tool_calls:
            logger.info(f"🔍 Handling tool call: {tool_call.tool_name}")
            if tool := self.tools_dict.get(tool_call.tool_name):
                try:
                    tool_call_result = tool(** tool_call.tool_kwargs)
                    step = ObservationReasoningStep(observation=tool_call_result.content)
                    logger.info(f"🔍 Tool call result: {step.observation}")
                except Exception as e:
                    step = ObservationReasoningStep(observation=f"Error calling tool {tool.metadata.get_name}: {e}")
            else:
                step = ObservationReasoningStep(
                  observation=f"Tool {tool_call.tool_name} does not exist"
              )
            
            steps = await ctx.store.get("steps", default=[])
            steps.append(step)
            
        return PrepEvent()


