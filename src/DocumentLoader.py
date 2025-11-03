import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    PyPDFDirectoryLoader,
    WebBaseLoader,
    TextLoader,
    DirectoryLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    YoutubeLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter
from langchain.schema.document import Document
from database.QdrantDB import QdrantDB
import time
import bs4
import logging
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv(override=True)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP"))


class DocumentLoader:
    """Create a DocumentLoader to load and split documents into chunks of Documents"""

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        data_dir: str = None,
        urls: list = None,
        files: list = None,
        yt_urls: list = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.data_dir = data_dir
        self.docs: list[Document] = []

        self.files = files
        self.yt_urls = yt_urls if yt_urls else []
        self.urls = urls if urls else []

        logging.info(f"Data dir: {data_dir}, content: {os.listdir(data_dir)}")
        logging.info(f"Urls: {urls}")

        if data_dir:
            self.load_directory()
        if urls:
            self.load_url_documents()
        if files:
            self.load_files()
        if yt_urls:
            self.load_youtube_vid()

        self.docs_chunks: list[Document] = self.get_chunks()

    def load_files(self):
        """Files loader based on different loader"""
        for file in self.files:
            if file.endswith(".pdf"):
                self.docs += PyPDFLoader(file).load()
            elif file.endswith(".txt"):
                self.docs += TextLoader(file, autodetect_encoding=True).load()
            elif file.endswith(".md"):
                self.docs += UnstructuredMarkdownLoader(file).load()
            elif file.endswith(".html"):
                self.docs += UnstructuredHTMLLoader(file).load()
            else:
                logging.warning(f"Unsupported file format: {file}")
                print(f"Unsupported file format: {file}")

    def load_directory(self):
        """Directory loader"""
        self.docs += DirectoryLoader(self.data_dir, glob=["*.txt", "*.md"]).load()
        self.docs += PyPDFDirectoryLoader(self.data_dir).load()
        for file in os.listdir(self.data_dir):
            if file.endswith(".html"):
                file_path = os.path.join(self.data_dir, file)
                self.docs += UnstructuredHTMLLoader(file_path).load()

    def load_youtube_vid(self):
        """Youtube videos loader"""
        for yt_url in self.yt_urls:
            vid_id = yt_url.split("v=")[-1].split("&")[0]
            self.docs += YoutubeLoader(video_id=vid_id, add_video_info=False).load()

    def load_url_documents(self):
        """Load HTML documents from URLs"""
        url_docs = []
        for url in self.urls:
            try:
                loader = WebBaseLoader(url)
                docs = loader.load()
                url_docs.extend(docs)
                logging.info(f"Loaded document from URL: {url}")
            except Exception as e:
                logging.error(f"Failed to load document from {url}: {e}")
                print(f"Failed to load document from {url}: {e}")
        self.docs += url_docs

    def split_documents(self) -> list[Document]:
        """Split loaded documents into chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=True,
            add_start_index=False,
            strip_whitespace=True,
        )
        return text_splitter.split_documents(self.docs)

    def get_chunks(self) -> list[Document]:
        """Split document into chunks with unique chunk_ids for each chunk based on its source and position

        Return:
            [
                {
                    page_content=''
                    metadata={
                        id=
                        chunk_id
                        source=''
                        page=
                        created_at=
                    }
                }
            ]
        """
        chunks: list[Document] = self.split_documents()

        last_page_id = None
        current_chunk_index = 0

        for i, chunk in enumerate(chunks):
            # source = chunk.metadata.get("source", "").split("\\")[-1].split("//")[-1]
            source_path = chunk.metadata.get("source", "")
            source = os.path.basename(source_path)
            page = chunk.metadata.get("page", 0)
            current_page_id = f"{source}:{page}"
            if current_page_id == last_page_id:
                current_chunk_index += 1
            else:
                current_chunk_index = 0
            chunk_id = f"{current_page_id}:{current_chunk_index}"
            last_page_id = current_page_id

            # chunk.metadata["id"] = chunk_id # Note Qdrant can only use 64-bit unsigned integers and UUID, not string
            chunk.metadata["id"] = str(uuid4())
            chunk.metadata["chunk_id"] = chunk_id
            chunk.metadata["source"] = source
            chunk.metadata["page"] = page
            chunk.metadata["created_at"] = time.strftime("%Y%m%d_%H%M%S")
            logging.info(f"Processed chunk metadata: {chunk.metadata}")

        return chunks


if __name__ == "__main__":
    chunks = DocumentLoader().docs_chunks
    if chunks:
        vector_db = QdrantDB(collection_name="test")
        vector_db.add_chunks(chunks)
