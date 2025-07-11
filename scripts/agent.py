import asyncio
from nt import system
from llama_index.llms.ollama import Ollama
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow import (
    FunctionAgent, 
    ToolCallResult, 
    ToolCall)
from llama_index.core.workflow import Context

import sys
import subprocess
import os
from pathlib import Path

SYSTEM_PROMPT = """
You are a helpful assistant that can work with our database software.
"""

llm = Ollama(
    model="llama3.1:latest",
    context_window=10000,
    max_tokens=2500,
    temperature=0.6,
    request_timeout=120.0,
)

async def get_agent(tools: McpToolSpec):
    tools = await tools.to_tool_list_async()
    agent = FunctionAgent(
        name="Agent",
        description="An agent that can work with Our Database software.",
        tools=tools,
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent



async def handle_user_message(
    message_content: str,
    agent: FunctionAgent,
    agent_context: Context,
    verbose: bool = False,
):
    handler = agent.run(message_content, ctx=agent_context)
    async for event in handler.stream_events():
        if verbose and type(event) == ToolCall:
            print(f"Calling tool {event.tool_name} with kwargs {event.tool_kwargs}")
        elif verbose and type(event) == ToolCallResult:
            print(f"Tool {event.tool_name} returned {event.tool_output}")

    response = await handler
    return str(response)



async def main():
    subprocess.Popen([sys.executable, "mcp/mcp_server.py"])
    mcp_client = BasicMCPClient(f"http://127.0.0.1:8000/sse")
    mcp_tools =  McpToolSpec(client=mcp_client)
    print("Server is running...")
    agent = await get_agent(mcp_tools)
    agent_context = Context(agent)
    print("Agent is ready...")
    while True:
        user_input = input("What would you like to do?")
        response = await handle_user_message(user_input, agent, agent_context,verbose=True)
        print(response)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)