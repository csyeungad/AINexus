import os
import logging
from langchain_ollama import OllamaEmbeddings
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import FlashrankRerank
from langchain.schema.document import Document
from langchain_qdrant import QdrantVectorStore
from database.QdrantDB import QdrantDB

OLLAMA_EMBED_URL = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME")
QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
SEMANTIC_WEIGHT = float(os.getenv("SEMANTIC_WEIGHT", 0.6))
KEYWORD_WEIGHT = float(os.getenv("KEYWORD_WEIGHT", 0.4))
TOP_K = int(os.getenv("TOP_K", 5))
SEMANTIC_SCORE = float(os.getenv("SEMANTIC_SCORE", 0.5))
RERANKER_SCORE = float(os.getenv("RERANKER_SCORE", 0.5))
TOP_N = int(os.getenv("TOP_N", 5))


class Retriever:
    def __init__(self):
        # Initialize model and embeddings
        self.embedding_function = OllamaEmbeddings(model=EMBED_MODEL_NAME, base_url=OLLAMA_EMBED_URL)
        # Custom class
        self.db = QdrantDB(collection_name=COLLECTION_NAME)
        # LangChain Qdrant class
        self.vector_store = QdrantVectorStore(
            client=self.db.client,
            collection_name=COLLECTION_NAME,
            embedding=self.embedding_function,
        )
        
        self.compression_retriever = None
        self.create_compression_retriever()

    def create_compression_retriever(self):
        """Create EnsembleReranker retriever by re-index all documents"""
        try:

            # Initialize ensemble retriever (semantic + keyword)
            retriever = self.vector_store.as_retriever(
                search_type="similarity_score_threshold", search_kwargs={"k": TOP_K, "score_threshold": SEMANTIC_SCORE}
            )    

            all_doc_chunks = self.db.get_all_docs()

            if not all_doc_chunks:
                logging.info(f"Fail to init compression_retriever: No documents in Vector DB, use vector store instead.")
                print(f"Fail to init compression_retriever: No documents in Vector DB, use vector store instead.")
                self.compression_retriever = retriever
                return False

            bm25_retriever = BM25Retriever.from_documents(all_doc_chunks)
            bm25_retriever.k = TOP_K
            logging.info(f"Indexed bm25_retriever for {len(all_doc_chunks)} chunks")
            print(f"Indexed bm25_retriever for {len(all_doc_chunks)} chunks")


            ensemble_retriever = EnsembleRetriever(
                retrievers=[bm25_retriever, retriever], weights=[KEYWORD_WEIGHT, SEMANTIC_WEIGHT]
            )
            # Initialize reranker
            compressor = FlashrankRerank(top_n=TOP_N)
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=ensemble_retriever
            )
            logging.info(f"retriever: {retriever}")
            logging.info(f"bm25_retriever: {bm25_retriever}")
            logging.info(f"ensemble_retriever: {ensemble_retriever}")
            logging.info(f"reranker: {compressor}")
            logging.info(f"compression_retriever: {compression_retriever}")

            self.compression_retriever = compression_retriever
            return True

        except Exception as e:
            logging.info(f"Failed to create compressor: {e}")
            print(f"Failed to create compressor: {e}")
            return False

    def invoke(self, query) -> list[Document]:
        """Get top retrieved documents from compressor"""
        return self.compression_retriever.invoke(query)

    def invoke_with_score_filter(self, query) -> list[Document]:
        """Get Filtered top retrieved documents from compressor"""
        docs = self.invoke(query)
        filter_docs = [doc for doc in docs if float(doc.metadata.get("relevance_score")) > RERANKER_SCORE]
        return filter_docs


retriever = Retriever()
retriever.create_compression_retriever()
