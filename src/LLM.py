import os
import logging
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.document import Document

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME")


RAG_TEMPLATE = """
You are an assistant for question-answering tasks. Answer the question based on the following context.
1. Use the following pieces of retrieved context to answer the question.
2. When answering question, make sure that your reponse are based on the provided information and use it as a reference.
3. If you don't know the answer, do not make up an answer.
4. Provide a clear and concise response, citing relevant information from the context.

**Context**:
{context}

Question: {question}
"""

class LLM:
    def __init__(self):
        self.model = ChatOllama(model=MODEL_NAME, temperature=0.7, base_url=OLLAMA_URL)

    @staticmethod
    def construct_prompt(docs: list[Document], query):
        """Construct query and retrieved docs in prompt template"""
        rag_prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)
        format_docs = "\n\n".join(
            (
                f"**Source**:\n{doc.metadata['source']}\n"
                f"**Relevance score**:{doc.metadata.get('relevance_score', 'N/A'):.5f}"
                f"**Content**:\n{doc.page_content}\n"
            )
            for doc in docs
        )
        prompt = rag_prompt.format(context=format_docs, question=query)
        return prompt


llm = LLM()
