import os
from notion_client import Client
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb

"""
Originally, I wanted to use Notion MCP tools to fetch the existing session for context for the summary generation. However, there are issue with the LLM using the Tools incorrectly and hallucinating, despite having the ability to reach the Notion database. 
For this use case, it's simpler to just fetch the recent session notes from the Notion database directly in Python. We will use chromadb to store the notes in vector database and retrieve relevant context for the summary generation.
This will also update the database after each session (fetch only the new session).
Sources: 
https://realpython.com/chromadb-vector-database/
https://realpython.com/courses/vector-databases-embeddings-chromadb/
"""


load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")
model = SentenceTransformer("all-MiniLM-L6-v2")
notion = Client(auth=NOTION_TOKEN)
CHROMA_DB_PATH = "chroma_data/"
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection("session_notes")

def get_page_text(page_id):
    text_content = []
    cursor = None
    # get page title pages[-1]["child_page"]["title"]
    page_title = notion.pages.retrieve(page_id)["properties"]["title"]["title"][0]["plain_text"]
    text_content.append(f"# {page_title}")

    while True:
        response = notion.blocks.children.list(block_id=page_id, start_cursor=cursor)
        
        for block in response['results']:
            # Extract text from different block types
            if block['type'] == 'paragraph':
                text = ''.join([t['plain_text'] for t in block['paragraph']['rich_text']])
                if text:
                    text_content.append(text)
            
            elif block['type'] == 'bulleted_list_item':
                text = ''.join([t['plain_text'] for t in block['bulleted_list_item']['rich_text']])
                if text:
                    text_content.append(f"- {text}")
            
            elif block['type'] == 'numbered_list_item':
                text = ''.join([t['plain_text'] for t in block['numbered_list_item']['rich_text']])
                if text:
                    text_content.append(f"1. {text}")
        
        if not response['has_more']:
            break
        cursor = response['next_cursor']
    
    return '\n'.join(text_content)
    

def get_all_sessions():
    pages = []
    cursor = None
    while True:
        kwargs = {"block_id": PAGE_ID, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
            
        response = notion.blocks.children.list(**kwargs)
        # filter only page blocks (skip dividers, headings etc)
        page_blocks = [b for b in response["results"] if b["type"] == "child_page"]
        pages.extend(page_blocks)
        
        if not response["has_more"]:
            break
        cursor = response["next_cursor"]
    
    return pages

def build_or_update_vector_db():
    pages = get_all_sessions()
    print(f"Found {len(pages)} session notes in Notion database.")
    existing = set(collection.get()["ids"])
    print(f"Already indexed: {len(existing)} sessions")
    new_session = 0
    for page in pages:
        if page["id"] not in existing:
            text = get_page_text(page["id"])
            embedding = model.encode(text).tolist()
            collection.add(ids=[page["id"]], embeddings=[embedding], metadatas=[{"text": text}])
            new_session += 1
    print(f"New sessions indexed: {new_session}")


if __name__ == "__main__":
    build_or_update_vector_db()