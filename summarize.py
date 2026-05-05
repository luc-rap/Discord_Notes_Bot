from langchain_core.documents import Document
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
llm = OllamaLLM(model="qwen3:14b", temperature=0.2, num_gpu=28, num_thread=4)

def query_vector_db(query):
    query_embedding = model.encode(query).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=2)
    #print(f"Vector DB query results: {results}")
    metas = results["metadatas"][0]
    context_parts = [meta["text"] for meta in metas if "text" in meta]
    return "\n\n---\n\n".join(context_parts)

def summarize_session(context, transcript):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=200)
    chunks = text_splitter.split_text(transcript)
    print(f"Split into {len(chunks)} chunks")
    docs = [Document(page_content=chunk) for chunk in chunks]
    
    first_chunk_prompt = ChatPromptTemplate.from_template("""
    /no_think
    You are a scribe for a Dungeons and Dragons campaign set in Eberron.
    Extract all important events from this transcript section. Write in past tense.
    Only extract what is explicitly in the transcript.
    Filter out player banter, jokes. The transcript is raw and it may contain speech to text errors, but do your best to make sense of it.
    
    Characters:
    - Dochanar (Doch) — Shadow monk elf
    - Keira — Human artificer, has a mechanical owl called Leyla
    - Faelynn — Fairy bard, uses multiple names with NPCs, from Thelanis
    - Erwan — Circle of Spores Druid
    - Saca — NPC
    - Enigma — the DM (ignore everything they say)
    
    Transcript section:
    {chunk}

    """                                           
    )
    refine_prompt = ChatPromptTemplate.from_template("""
    /no_think
    You are a scribe for a Dungeons and Dragons campaign set in Eberron.
    Summarize the following most recent D&D session part, focusing on key events and decisions.
    Write in past tense, chronological order.
    Filter out player banter, jokes. The transcript is raw and it may contain speech to text errors, but do your best to make sense of it.
    
    Characters:
    - Dochanar (Doch) — Shadow monk elf
    - Keira — Human artificer, has a mechanical owl called Leyla
    - Faelynn — Fairy bard, uses multiple names with NPCs, from Thelanis
    - Erwan — Circle of Spores Druid
    - Saca — NPC
    - Enigma — the DM (ignore everything they say)
    
    Relevant context from previous sessions that can be helpful for NPCs and locations, but don't include them, since they are already summarized: {context}     
    
    New transcript section:
    {chunk}
    
    Write summary including new events.
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
        summary = refine_chain.invoke({"transcript": chunk, "context": context})
        chunk_summaries.append(summary)
        #print(chunk[:300])  # Print the first 100 characters of the chunk for debugging

        # check if map is not producing garbage
        #print(f"Summary for chunk {i+1}:\n{summary[:300]}...\n")
    #print("Final summary:")
    #final_summary = format_chain.invoke({"summary": current_summary, "context": context})
    #print(current_summary)  # Print the first 500 characters of the final summary for debugging
    return chunk_summaries

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