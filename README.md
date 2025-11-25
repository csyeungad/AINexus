# AINexus

## Introduction

This project allows users to run Retrieval Augmentation Generation (RAG) using locally hosted models.

RAG effectively combines retrieval and generation techniques, enabling the chatbot to deliver accurate and context-aware responses. Leveraging semantic search and keyword search, followed by a reranker to get the top most relevant documents as context for QA.

## Local hosting services (LLM, embedding models, vector database)

1. Use docker to run the ollama service

   You could use Ollama to host AI model locally through
   https://ollama.com/download

   ``` bash
   docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
   ```

2. Use docker to run the qdrant vector database service

   ``` bash
   docker run -d \
   --name qdrant \
   -p 6333:6333 \
   -v qdrant_data:/qdrant/storage \
   qdrant/qdrant
   ```

## Installation and quick start

1. Using conda

   To install the required dependencies, run:

   ```sh
   conda create -n rag python==3.9.21 -y
   conda activate rag
   pip install -r requirements.txt
   ```

   Then start the software with

   ```sh
   streamlit run src\app.py
   ```

2. Using uv

   To install the required dependencies, run:

   ```sh
   uv sync
   ```

   Then start the software with

   ```sh
   uv run streamlit run src\app.py
   ```

## Set up `.env` configuration

Set the following configuration parameters:

```python
# Model
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME="qwen3_30B_A3B_ctx_8K" # LLM model for chat
EMBED_MODEL_NAME="nomic-embed-text" # Embedding model for documents

# Qdrant vector database
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "test"

# DocumentLoader
CHUNK_SIZE = 800
CHUNK_OVERLAP = 50

# Semantic Retriever
TOP_K = 12
SEMANTIC_SCORE = 0.6

# Ensemble Retriever
SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4

# Reranker
TOP_N = 6
RERANKER_SCORE = 0.7
```

## Usage

1. **Upload Documents:**

   - Navigate to the "Upload Documents" page.
   - Select and upload multiple files (PDF, TXT, MD, HTML).
   - Choose different chunk size and overlap size.
   - Split the documents into chunks and display them before uploading to the database.

2. **View and Delete Documents:**

   - Navigate to the "Knowledge Base" page.
   - View all the chunks available in the vector database.
   - Delete documents as needed.

3. **Chat with the Content:**

   - Navigate to the "Chat" page.
   - Enter your query in the chat input.
   - The chatbot will respond based retrieved documents.
