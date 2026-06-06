from datetime import datetime
from langchain_core.documents import Document
import chromadb
# from sentence_transformers import SentenceTransformer
from langchain_ollama import OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# model = SentenceTransformer("all-MiniLM-L6-v2")
CHROMA_DB_PATH = "chroma_data/"
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection("session_notes")
llm = OllamaLLM(model="qwen3:14b", temperature=0.2, num_gpu=28, num_thread=4)

def query_vector_db(query):
    # query_embedding = model.encode(query).tolist()
    # results = collection.query(query_embeddings=[query_embedding], n_results=3)
    # #print(f"Vector DB query results: {results}")
    # metas = results["metadatas"][0]
    # context_parts = [meta["text"] for meta in metas if "text" in meta]
    # return "\n\n---\n\n".join(context_parts)
    pass

def summarize_session(transcript):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=100)
    chunks = text_splitter.split_text(transcript)
    print(f"Split into {len(chunks)} chunks")
    docs = [Document(page_content=chunk) for chunk in chunks]
    
    first_chunk_prompt = ChatPromptTemplate.from_template("""
    /no_think
    You are a scribe for a Dungeons and Dragons campaign set in Eberron.
    You receive a transcript, that is divided into smaller chunks. Write summary for each chunk (they have a small overlap so you can have better understanding of the context). Focus on key events and decision. Write in past tense, chronological order.
    Only extract what is explicitly in the transcript.
    Filter out player banter, jokes. The transcript is raw and it may contain speech to text errors, but do your best to make sense of it. It also has speaker diarization, so you can identify who is talking when
    
    Characters:
    - Dochanar (Doch) — Shadow monk elf
    - Keira — Human artificer, has a mechanical owl called Leyla
    - Faelynn — Fairy bard, uses multiple names with NPCs, from Thelanis
    - Erwan — Circle of Spores Druid
    - Saca — NPC, not a Speaker in the transcript, but mentioned multiple times
    - Enigma = the DM
    
    Transcript chunk:
    {chunk}

    """                                           
    )
    refine_prompt = ChatPromptTemplate.from_template("""
    /no_think
    You are a scribe for a Dungeons and Dragons campaign set in Eberron. You take notes from the session transcript. You receive a transcript, that is divided into smaller chunks. Write summary for each chunk (they have a small overlap so you can have better understanding of the context). Focus on key events and decision. Write in past tense, chronological order. Skip out player banter, jokes and other non-essential content not related to DnD. There might be some out-of-character discussions. The transcript is raw and it may contain speech to text errors (especially names). Use the context to understand the story and characters, but only extract what is explicitly in the transcript. Keep it simple, clear, concise. At the end of the chunk, type "CHUNK END" so that when I combine the summaries, I can understand where the chunk ends.
    Players' characters for reference: (use this to understand who is who, but don't add any information that is not explicitly in the transcript, and use the names since they might be different in the transcript due to speech to text errors):
    - Dochanar (Doch) — Shadow monk elf
    - Keira — Human artificer, has a mechanical owl called Leyla
    - Faelynn — Fairy bard, uses multiple names with NPCs, from Thelanis
    - Erwan — Circle of Spores Druid
    - Saca — NPC, not a Speaker in the transcript, but mentioned multiple times
    - Enigma = the DM    
    New transcript section:
    {chunk}
    """)
    
    format_prompt = ChatPromptTemplate.from_template("""
    /no_think
    You are a scribe for a Dungeons and Dragons campaign set in Eberron.
    Format this raw session summary into a polished final version.
    Do not remove or skip any details. Use the context to correctly identify NPCs and locations.
    
    ## Previous sessions context (reference only — do not summarize):
    {context}
    
    ## Raw summary to format:
    {summary}
    
    Format as:
    ### Narrative Summary
    (4-6 detailed paragraphs covering beginning, middle and end equally)
    
    ### Key Events
    (chronological bullet list, minimum 8 items)
    
    ### NPCs Encountered
    (name + what happened with them)
    
    ### Player Decisions
    (what choices were made and why they matter)
    
    ### Cliffhanger
    (how the session ended)
    
    Write final polished summary.
""")
    
    #first_chain = first_chunk_prompt | llm | StrOutputParser()
    refine_chain = refine_prompt | llm | StrOutputParser()
    #format_chain = format_prompt | llm | StrOutputParser()
    
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)} with length {len(chunk)}")
        summary = refine_chain.invoke({"chunk": chunk})
        chunk_summaries.append(summary)
        #print(chunk[:300])  # Print the first 100 characters of the chunk for debugging

        # check if map is not producing garbage
        #print(f"Summary for chunk {i+1}:\n{summary[:300]}...\n")
    #print("Final summary:")
    #final_summary = format_chain.invoke({"summary": current_summary, "context": context})
    #print(current_summary)  # Print the first 500 characters of the final summary for debugging
    return chunk_summaries

#if __name__ == "__main__":
    #context = query_vector_db(transcript)
    #print("Queried vector database for relevant context.")
    #response = summarize_session(transcript)
    #print("Generated summary using Ollama.")
    #print("\n--- SUMMARY ---")
    #current_date = datetime.now().strftime("%Y-%m-%d")
    #filename = f"summary_{current_date}.txt"
    #with open(filename, "w") as f:
    #    f.write("\n\n---\n\n".join(response))   
    #print(f"Summary saved to {filename}")
    
    ##TODO title = input("\nEnter session title (e.g. '24/06/24 (Session 35)'): ").strip()
    ##TODO save summary to Notion/Discord/File/etc 
    # Fetch recent session directly, and older relevant from vector DB?//fetching last session is probably more reliable, vector DB is returning unrelated context which is the LLM adding to the summary