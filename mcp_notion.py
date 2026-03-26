import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
import ollama

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

server_params = StdioServerParameters(
    command="docker",
    args=[
        "run", "--rm", "-i",
        "-e", "NOTION_TOKEN",
        "mcp/notion"
    ],
    env={"NOTION_TOKEN": NOTION_TOKEN}
)

async def list_tools():
    print("Connecting to MCP server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"{tool.name}: {tool.description}")

#asyncio.run(list_tools())

async def ollama_notion_integration(prompt="Confirm that Notion is connected correctly, and tell me the name of the Notion. The page_id is . Try to retrieve page information using the page_id."):
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await session.list_tools()
            ollama_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                for tool in mcp_tools.tools
            ]

            print(f"Giving Ollama access to {len(ollama_tools)} Notion tools...")
            
            response = ollama.chat(
                model="qwen3.5",
                messages=[{"role": "user", "content": prompt}],
                tools=ollama_tools,
                options={
                    "num_gpu": 10,
                }
                
            )
            
            message = response["message"]
            print(f"Ollama response: {message}")
            
            if "tool_calls" in response:
                for call in response["tool_calls"]:
                    print(f"Ollama called tool {call['name']} with arguments {call['arguments']}")
                    result = await session.call_tool(name=call["name"], arguments=call["arguments"])
                    print(f"Result from MCP tool call: {result}")

asyncio.run(ollama_notion_integration())