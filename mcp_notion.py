import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
import ollama
from openai import OpenAI
import lmstudio as lms

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

# asyncio.run(list_tools())

async def ollama_notion_integration(prompt):
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

            messages = [{"role": "user", "content": prompt}, {"role": "system", "content": "You have access to Notion MCP tools. Always use them to answer the user's question. Don't use raw API calls, only the provided tools. Don't pass API headers."}]

            print("Starting agentic loop...\n")
            iteration = 0

            while True:
                iteration += 1
                print(f"--- Iteration {iteration} ---")

                response = client.chat.completions.create(
                    model="qwen3.5:9b",
                    messages=messages,
                    tools=ollama_tools
                )

                message = response.choices[0].message
                messages.append(message)

                if not message.tool_calls:
                    print(f"\nFinal answer: {message.content}")
                    break

                for call in message.tool_calls:
                    tool_name = call.function.name
                    tool_args = json.loads(call.function.arguments)
                    print(f"  → Calling tool: {tool_name}")
                    print(f"    Args: {json.dumps(tool_args, indent=2)}")

                    result = await session.call_tool(name=tool_name, arguments=tool_args)
                    result_text = result.content[0].text if result.content else "{}"
                    print(f"    Result: {result_text[:200]}...")  # truncate for readability

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result_text
                    })

asyncio.run(ollama_notion_integration("Confirm that Notion is connected correctly, and tell me the name of the Notion. You MUST use the available Notion MCP tools to answer this. Use API-retrieve-a-database."))