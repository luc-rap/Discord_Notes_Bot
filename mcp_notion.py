import asyncio
import threading
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
import lmstudio as lms

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

server_params = StdioServerParameters(
    command="docker",
    args=["run", "--rm", "-i", "-e", "NOTION_TOKEN", "mcp/notion"],
    env={"NOTION_TOKEN": NOTION_TOKEN}
)

# Dedicated event loop in a background thread for async MCP calls
mcp_loop = asyncio.new_event_loop()
mcp_thread = threading.Thread(target=mcp_loop.run_forever, daemon=True)
mcp_thread.start()

def run_async(coro):
    """Run an async coroutine from sync code using the background loop."""
    print("[DEBUG] run_async: submitting coroutine to mcp_loop")
    future = asyncio.run_coroutine_threadsafe(coro, mcp_loop)
    print("[DEBUG] run_async: waiting for result...")
    result = future.result()  # blocks here if stuck
    print(f"[DEBUG] run_async: got result: {str(result)[:100]}")
    return result


async def agentic_notion(prompt: str):
    main_loop = asyncio.get_event_loop()  # capture main loop
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[DEBUG] MCP session initialized")

            # Wrap all MCP tools as plain Python functions
            mcp_tools = await session.list_tools()
            def make_tool_fn(tool):
                async def _call(**kwargs):
                    print(f"[DEBUG] calling MCP tool '{tool.name}' with {kwargs}")
                    result = await session.call_tool(name=tool.name, arguments=kwargs)
                    print(f"[DEBUG] MCP returned: {str(result)[:100]}")
                    return result.content[0].text if result.content else "{}"
                
                def tool_fn(**kwargs):
                    print(f"[DEBUG] tool_fn '{tool.name}' invoked")
                    # submit to main loop where MCP session lives
                    future = asyncio.run_coroutine_threadsafe(_call(**kwargs), main_loop)
                    return future.result()

                tool_fn.__name__ = tool.name.replace("-", "_")
                tool_fn.__doc__ = tool.description
                return tool_fn
            
            tool_fns = [make_tool_fn(t) for t in mcp_tools.tools]
            print(f"[DEBUG] Wrapped {len(tool_fns)} tools")

            model = lms.llm("qwen/qwen3.5-9b")  # match model name in LM Studio
            print("[DEBUG] Starting act() in executor...")
            # .act() handles the entire agentic loop automatically
            await main_loop.run_in_executor(
                None,
                lambda: model.act(
                    prompt,
                    tool_fns,
                    on_message=lambda msg: print(f"\n[MESSAGE {msg.role}]: {msg.content or '(tool call)'}"),
                    on_round_start=lambda i: print(f"[DEBUG] Round {i} starting..."),
                    on_round_end=lambda i: print(f"[DEBUG] Round {i} ended"),
                )
            )
            print("[DEBUG] act() completed")

asyncio.run(agentic_notion(
    "Confirm you can access MCP Notion correctly and tell me its name. Use the tools as needed."
))