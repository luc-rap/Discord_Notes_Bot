import chromadb
from sentence_transformers import SentenceTransformer
from langchain_ollama import OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


model = SentenceTransformer("all-MiniLM-L6-v2")
CHROMA_DB_PATH = "chroma_data/"
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection("session_notes")
llm = OllamaLLM(model="qwen3:8b", temperature=0.2, num_gpu=20, num_thread=8)

def query_vector_db(query):
    query_embedding = model.encode(query).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=5)
    #print(f"Vector DB query results: {results}")
    metas = results["metadatas"][0]
    context_parts = [meta["text"] for meta in metas if "text" in meta]
    return "\n\n---\n\n".join(context_parts)

def summarize_session(context, transcript):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=200)
    chunks = text_splitter.split_text(transcript)
    print(f"Split into {len(chunks)} chunks")
    
    map_prompt = ChatPromptTemplate.from_template("""
    /no_think
    Summarize the following most recent D&D session part, focusing on key events and decisions.
    Filter out player banter, jokes, dice rolls, and meta-discussion.
    Characters:
    - Dochanar (Doch) — Shadow monk elf
    - Keira — Human artificer, has a mechanical owl called Leyla  
    - Faelynn — Fairy bard, uses multiple names with NPCs, from Thelanis
    - Erwan — Circle of Spores Druid
    - Saca — NPC
    - Enigma — the DM
    Transcript section: {transcript}
    Relevant context from previous sessions that can be helpful, but don't need to be included, since they are already summarized: {context}          
    """                                           
    )
    reduce_prompt = ChatPromptTemplate.from_template("""
    /no_think                                                 
    You are a scribe for a D&D campaign set in Eberron.
    Combine the following summaries of transcript sections into a single coherent summary.
    Filter out player banter, jokes. 
    Structure:
    ### Narrative Summary
    ### Key Events
    ### NPCs Encountered
    ### Player Decisions
    ### Cliffhanger
    Raw notes:
        {text}
    Final summary:
    """)
    
    map_chain = map_prompt | llm | StrOutputParser()
    reduce_chain = reduce_prompt | llm | StrOutputParser()
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)} with length {len(chunk)}")
        summary = map_chain.invoke({"transcript": chunk, "context": context})
        chunk_summaries.append(summary)
    
    final_summary = reduce_chain.invoke({"text": "\n\n---\n\n".join(chunk_summaries)})
    return final_summary

if __name__ == "__main__":

    with open("transcript_2.txt", "r") as f:
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
    # Fetch recent session directly, and older relevant from vector DB?