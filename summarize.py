import chromadb
import ollama
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
CHROMA_DB_PATH = "chroma_data/"
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection("session_notes")

def query_vector_db(query):
    query_embedding = model.encode(query).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=5)
    print(f"Vector DB query results: {results}")
    metas = results["metadatas"][0]
    context_parts = [meta["text"] for meta in metas if "text" in meta]
    return "\n\n---\n\n".join(context_parts)

def summarize_session(context, transcript):
    prompt = f"""
    Relevant context for summarizing the Dungeons and Dragons session: 
    {context}
 
    Here is the transcript of the new session:

    --- TRANSCRIPT START ---
    {transcript}
    --- TRANSCRIPT END ---

    Additional information that may be useful for summarization, but it's not necessary to include all of it in the summary. Use your judgment to decide what is relevant:
    Main characters:

    Dochanar - sometimes referred to as Doch. Shadow monk elf. He comes from a distant village. 

    Keira - Human artificer. She is a member of the Artisan Guild and she was living in Aundair. She has a mechanical owl called Leyla.

    Faelynn - fairy bard. She uses multiple different names when talking to new NPCs for her own reason. She comes from Thelanis. 

    Erwan - Circle of Spores Druid

    Saca - NPC

    Enigma = DM

    The transcript is a raw record, including player banters, jokes, off-topic discussions. Focus on the key events of the session, decisions and important interactions. Since it is a speech-to-text, it may contain errors or misinterpretations. Use your judgment to filter out noise and focus on the meaningful content.
     Do not focus only on recent events. The session start is just as important as the end. The summary should be detailed and comprehensive.
    """
    response = ollama.chat(
        model="llama3.1:8b", 
        messages=[
            {"role": "system", "content": """
             You are a scribe that writes detailed summaries of Dungeons and Dragons sessions from start to finish equally. Write a detailed session summary based on the provided context and transcript. Focus on key events, decisions, and interactions. Ignore off-topic discussions and banter. Read the ENTIRE transcript from start to finish before writing anything. Your summary MUST cover events from the BEGINNING, MIDDLE, and END of the session equally. Do not focus only on recent events. The session start is just as important as the end. The summary should be detailed and comprehensive.
             """
             },
            {"role": "user", "content": prompt}
        ],
        options={"num_gpu": 1, "num_threads": 4,  "temperature": 0.2} # "num_ctx": 32768,
    )
    
    return response.message.content

if __name__ == "__main__":
    with open("transcript.txt", "r") as f:
        transcript = f.read()
    print("Loaded transcript from file with length:", len(transcript))
    context = query_vector_db(transcript)
    print("Queried vector database for relevant context.")
    response = summarize_session(context, transcript)
    print("Generated summary using Ollama.")
    print("\n--- SUMMARY ---")
    print(response)
    
    ##TODO title = input("\nEnter session title (e.g. '24/06/24 (Session 35)'): ").strip()
    ##TODO save summary to Notion/Discord/File/etc 