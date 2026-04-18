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

with open("transcript.txt", "r") as f:
    transcript = f.read()
print(f"[DEBUG] Loaded transcript ({len(transcript)} chars)")
    
prompt = f"""You are a scribe for a D&D campaign. Your job is to:

1. Use existing session notes in the Notion MCP database to understand the context of the campaign and the current story arc. The session notes are in "Session Notes" and are organized by date and session number. Title in format: DD/MM/YY (Session N). Fetch the most recent sessions (3-5) to get the latest context (ordered from newest to oldest). If you need to, you can also fetch older sessions or search for specific NPCs or events mentioned in the transcript.
2. Read the transcript below and print the session summary


Here is the transcript of the new session:

--- TRANSCRIPT START ---
{transcript}
--- TRANSCRIPT END ---

Begin by fetching the existing session notes for context, then create the summary page. Use Notion MCP tools to interact with the database.
1. Tool: API_query_a_database to fetch recent session notes for context. Database_id = 24339ee9e57f43958ef750844d4cc6d6
2. Tool: API_get_block_children for page returned in step 1, fetch its content

Main characters:

Dochanar - sometimes referred to as Doch. Shadow monk elf. He comes from a distant village. 

Keira - Human artificer. She is a member of the Artisan Guild and she was living in Aundair. She has a mechanical owl called Leyla.

Faelynn - fairy bard. She uses multiple different names when talking to new NPCs for her own reason. She comes from Thelanis. 

Erwan - Circle of Spores Druid

Saca - NPC

Enigma = DM

The transcript is a raw record, including player banters, jokes, off-topic discussions. Focus on the key events of the session, decisions and important interactions. Since it is a speech-to-text, it may contain errors or misinterpretations. Use your judgment to filter out noise and focus on the meaningful content.
"""

prompt = "/no_think\n\n" + prompt

#TODO
#3. Create a new page in the same Notion database with:
#   - Title in format: DD/MM/YY (Session N) — infer date and session number from existing notes
#   - Full narrative summary in the page body
#   - Sections for: Key Events, NPCs Encountered, Player Decisions, Cliffhanger

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
                    #print(f"[DEBUG] MCP returned: {str(result)[:100]}")
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

            model = lms.llm("qwen/qwen3.5-9b", config={"context_length": 31000, "contextOverflowPolicy": "stopAtLimit"})  # match model name in LM Studio
            print("[DEBUG] Starting act() in executor...")
            # .act() handles the entire agentic loop automatically
            await main_loop.run_in_executor(
                None,
                lambda: model.act(
                    prompt,
                    tool_fns,
                    on_message=lambda msg: print(f"\n[ASSISTANT]: {msg.content}") if msg.role == "assistant" else None,
                    on_round_start=lambda i: print(f"[DEBUG] Round {i} starting..."),
                    on_round_end=lambda i: print(f"[DEBUG] Round {i} ended"),
                )
            )
            print("[DEBUG] act() completed")

asyncio.run(agentic_notion(prompt))