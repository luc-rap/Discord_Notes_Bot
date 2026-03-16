from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever

MODEL = "gemma2:9b"

model = OllamaLLM(model=MODEL)

template = """
"""
