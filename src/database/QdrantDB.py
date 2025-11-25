import os
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    PointIdsList,
    Filter,
    FieldCondition,
    MatchValue,
    OrderBy,
    Direction,
)
from langchain_ollama import OllamaEmbeddings
from langchain.schema.document import Document

QDRANT_URL = os.getenv("QDRANT_URL")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME")
OLLAMA_EMBED_URL = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434")  # Default to localhost if not set
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "test")  # Default to localhost if not set
NOLIMIT = 999999


class QdrantDB:
    def __init__(self, collection_name="test"):
        self.collection_name = collection_name
        self.embedding_function = OllamaEmbeddings(
            model=EMBED_MODEL_NAME,
            base_url=OLLAMA_EMBED_URL,  # Use custom Ollama server URL
        )
        self.client = QdrantClient(url=QDRANT_URL)

        self.vector_size = len(self.embedding_function.embed_query(".."))
        self.init_collection()

        logging.info(f"[QdrantDB] Using embedding function: {self.embedding_function}")
        logging.info(f"[QdrantDB] Embedding dimension: {len(self.embed_text('hi'))}")
        logging.info(f"[QdrantDB] Collection: {collection_name} count: {self.get_count()}")

    def init_collection(self):
        if not self.client.collection_exists(self.collection_name):
            res = self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
            if res:
                logging.info(f"[QdrantDB] Collection {self.collection_name} created.")

    def reset_collection(self):
        if self.client.collection_exists(self.collection_name):
            try:
                if res := self.client.delete_collection(self.collection_name):
                    logging.info(f"[QdrantDB] Collection {self.collection_name} deleted.")
            except Exception as e:
                logging.info(f"[QdrantDB] No existing collection to delete: {e}")

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
        )

    def add_chunks(self, chunks: list[Document]) -> bool:
        """Add chunks to the Qdrant collection.
        Return true if success.
        """
        try:
            logging.info(f"[QdrantDB] Adding new documents: {len(chunks)}...")
            print(f"[QdrantDB] Adding new documents: {len(chunks)}...")

            embeddings = self.embed_documents([chunk.page_content for chunk in chunks])
            # print(len(chunks))
            # print(len(embeddings))
            # print(len(embeddings[0]))

            points = [
                PointStruct(
                    id=chunk.metadata["id"],
                    vector=embedding,
                    payload={"content": chunk.page_content, "metadata": chunk.metadata},
                )
                for embedding, chunk in zip(embeddings, chunks)
            ]

            # points = []
            # for chunk in chunks:
            #     pointId = chunk.metadata["id"]
            #     embedding = self.embed_text(chunk.page_content)
            #     point = PointStruct(
            #         id = pointId,
            #         vector= embedding,
            #         payload= {
            #             "content": chunk.page_content,
            #             "metadata": chunk.metadata
            #         }
            #     )
            #     points.append(point)

            self.client.upsert(collection_name=self.collection_name, points=points)

            print(f"[QdrantDB] Total count after adding: {self.get_count()}.")
            logging.info(f"[QdrantDB] Total count after adding: {self.get_count()}.")
            return True
        except Exception as e:
            print(f"[QdrantDB] Error adding documents: {e}")
            logging.error(f"[QdrantDB] Error adding documents: {e}")
            return False

    def embed_text(self, text: str) -> list:
        """Embed text using the embedding function."""
        return self.embedding_function.embed_query(text)

    def embed_documents(self, docs: list[str]) -> list[list[float]]:
        return self.embedding_function.embed_documents(docs)

    def get_count(self) -> int:
        """Get the count of documents in the Qdrant collection."""
        return self.client.count(collection_name=self.collection_name).count

    def get_all_documents(self) -> list:
        """Get all documents from the Qdrant collection."""
        # points = self.client.search(collection_name=self.collection_name, limit=NOLIMIT)[0]
        points = self.client.scroll(collection_name=self.collection_name, limit=NOLIMIT)[0]
        return [point.payload.get("content", "") for point in points]

    def get_all_metadatas(self) -> list:
        """Get all metadata from the Qdrant collection."""
        # points = self.client.search(collection_name=self.collection_name, limit=NOLIMIT)[0]
        points = self.client.scroll(collection_name=self.collection_name, limit=NOLIMIT)[0]
        return [point.payload.get("metadata", {}) for point in points]

    def get_all_ids(self, source: str = None) -> list:
        """Get all existing IDs in the Qdrant collection."""
        # points = self.client.search(collection_name=self.collection_name, limit=NOLIMIT)[0]
        if source:
            points = self.client.scroll(
                collection_name=self.collection_name,
                limit=NOLIMIT,
                with_payload=False,
                with_vectors=False,
                scroll_filter=Filter(must=[FieldCondition(key="metadata.source", match=MatchValue(value=source))]),
            )
            return [point.id for point in points[0]]

        points = self.client.scroll(collection_name=self.collection_name, limit=NOLIMIT)[0]
        return [point.id for point in points]

    def get_all_docs(self) -> list[Document]:
        """Get all exisit document as list of LangChain Document object"""
        count = self.get_count()
        if count == int(0):
            return []

        points = self.client.scroll(collection_name=self.collection_name, limit=NOLIMIT)[0]
        if not points:
            return []

        return [
            Document(page_content=point.payload.get("content", ""), metadata=point.payload.get("metadata", {}))
            for point in points
        ]

    def get_all_data(self, limit=NOLIMIT):
        count = self.get_count()
        if count == int(0):
            return None, None
        metadatas = self.get_all_metadatas()
        sources = list(dict.fromkeys([metadata["source"].split("\\")[-1].split("//")[-1] for metadata in metadatas]))
        # print(f"All Sources: {sources}")

        all_docs = []
        for src in sources:
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False,
                scroll_filter=Filter(must=[FieldCondition(key="metadata.source", match=MatchValue(value=src))]),
                # TODO: sort the chunks in order
                # order_by=OrderBy(
                #     key= 'metadata.start_index',
                #     # key= "metadata.page",
                #     direction= Direction.ASC,
                # )
            )
            docs = [point.payload["content"] for point in scroll_result[0]]
            all_docs.append(docs)

        # print(len(sources), len(all_docs), len(all_docs[0]))
        return sources, all_docs

    def delete_by_ids(self, ids: list):
        """Delete documents by their IDs."""
        try:
            self.client.delete(collection_name=self.collection_name, points_selector=PointIdsList(points=ids))
        except Exception as e:
            logging.error(f"[QdrantDB] Error deleting documents: {e}")
            print(f"[QdrantDB] Error deleting documents: {e}")

    def similarity_search_with_score(self, query_text, top_k=3, score_threshold=0.3):
        """Perform similarity search on query text with top_k results and score."""
        try:
            query_vector = self.embed_text(query_text)
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
                score_threshold=score_threshold,
            )
            results = [
                [
                    Document(
                        page_content=result.payload.get("content", ""), metadata=result.payload.get("metadata", {})
                    ),
                    result.score,
                ]
                for result in search_results
            ]
            sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
            return sorted_results if sorted_results else None
        except Exception as e:
            logging.error(f"[QdrantDB] Error in similarity search: {e}")
            print(f"[QdrantDB] Error in similarity search: {e}")
            return None

    def similarity_search(self, query_text, top_k=3):
        """Perform similarity search on query text with top_k results."""
        try:
            query_vector = self.embed_text(query_text)
            search_results = self.client.search(
                collection_name=self.collection_name, query_vector=query_vector, limit=top_k, with_payload=True
            )
            return [
                Document(page_content=result.payload.get("content", ""), metadata=result.payload.get("metadata", {}))
                for result in search_results
            ]
        except Exception as e:
            logging.error(f"[QdrantDB] Error in similarity search: {e}")
            print(f"[QdrantDB] Error in similarity search: {e}")
            return []


if __name__ == "__main__":
    log_dir = "./log"
    log_name = f"{os.path.basename(__file__).split('.')[0]}.log"
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    logging.basicConfig(
        filename=os.path.join(log_dir, log_name),
        level=logging.INFO,
        filemode="a",
        format=f"[%(asctime)s - %(levelname)s] : %(message)s",
    )

    database = QdrantDB(collection_name="streamlit_test")
    all_ids = database.get_all_ids()
    all_documents = database.get_all_documents()
    all_metadatas = database.get_all_metadatas()
    all_docs: list[Document] = database.get_all_docs()
    logging.info(f"Database collection count: {database.get_count()}")
    logging.info(f"Existing IDs: {database.get_all_ids()}")
    logging.info(f"Database documents count: {len(all_documents)}")
    logging.info(f"Example documents : {all_documents[0]}")
    logging.info(f"Database metadatas count: {len(all_metadatas)}")
    logging.info(f"Example metadatas : {all_metadatas[0]}")
    logging.info(f"Database docs count: {len(all_docs)}")
    logging.info(f"Example docs : {all_docs[0]}")
    logging.info(f"Embedding dimension: {len(database.embed_text('hi mario'))}")
