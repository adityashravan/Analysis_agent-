"""
Knowledge Base Manager
Handles ingestion of multiple source types: PDFs, text files, web pages, code
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# PDF Processing
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    import PyPDF2

# Web scraping
import requests
from bs4 import BeautifulSoup

# LangChain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """
    Manages knowledge base with multiple source types
    """
    
    def __init__(self, config, persist_directory: str = "./vector_store"):
        self.config = config
        self.persist_directory = persist_directory
        
        # Initialize embeddings (only OpenAI for now)
        embed_kwargs = {"openai_api_key": config.openai_api_key}
        if hasattr(config, 'openai_base_url') and config.openai_base_url:
            embed_kwargs["base_url"] = config.openai_base_url
        self.embeddings = OpenAIEmbeddings(**embed_kwargs)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Lazy-load vector store (only create when needed)
        self._vector_store = None
    
    @property
    def vector_store(self):
        """Lazy-load vector store on first access"""
        if self._vector_store is None:
            self._vector_store = self._load_or_create_vector_store()
        return self._vector_store
    
    def _load_or_create_vector_store(self):
        """Load existing or create new vector store"""
        if os.path.exists(self.persist_directory):
            logger.info(f"Loading existing vector store from {self.persist_directory}")
            return Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            logger.info("Creating new vector store")
            return Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
    
    def ingest_pdf(self, pdf_path: str, metadata: Optional[Dict] = None) -> int:
        """
        Ingest PDF document
        Returns number of chunks created
        """
        logger.info(f"Ingesting PDF: {pdf_path}")
        
        text = ""
        
        if HAS_PYMUPDF:
            # Use PyMuPDF (better extraction)
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        else:
            # Fallback to PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text()
        
        # Create document with metadata
        doc_metadata = metadata or {}
        doc_metadata.update({
            "source": pdf_path,
            "source_type": "pdf",
            "ingestion_date": datetime.utcnow().isoformat()
        })
        
        # Split and store
        chunks = self.text_splitter.split_text(text)
        documents = [
            Document(page_content=chunk, metadata=doc_metadata)
            for chunk in chunks
        ]
        
        self.vector_store.add_documents(documents)
        logger.info(f"Created {len(documents)} chunks from PDF")
        
        return len(documents)
    
    def ingest_text_file(self, file_path: str, metadata: Optional[Dict] = None) -> int:
        """
        Ingest text file (.txt, .md, etc.)
        Returns number of chunks created
        """
        logger.info(f"Ingesting text file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        doc_metadata = metadata or {}
        doc_metadata.update({
            "source": file_path,
            "source_type": "text",
            "ingestion_date": datetime.utcnow().isoformat()
        })
        
        chunks = self.text_splitter.split_text(text)
        documents = [
            Document(page_content=chunk, metadata=doc_metadata)
            for chunk in chunks
        ]
        
        self.vector_store.add_documents(documents)
        logger.info(f"Created {len(documents)} chunks from text file")
        
        return len(documents)
    
    def ingest_web_page(self, url: str, metadata: Optional[Dict] = None) -> int:
        """
        Scrape and ingest web page
        Returns number of chunks created
        """
        logger.info(f"Ingesting web page: {url}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks_text = '\n'.join(chunk for line in lines for chunk in line.split("  ") if chunk)
        
        doc_metadata = metadata or {}
        doc_metadata.update({
            "source": url,
            "source_type": "web",
            "ingestion_date": datetime.utcnow().isoformat()
        })
        
        chunks = self.text_splitter.split_text(chunks_text)
        documents = [
            Document(page_content=chunk, metadata=doc_metadata)
            for chunk in chunks
        ]
        
        self.vector_store.add_documents(documents)
        logger.info(f"Created {len(documents)} chunks from web page")
        
        return len(documents)
    
    def ingest_directory(self, directory: str, file_patterns: List[str] = None) -> Dict[str, int]:
        """
        Recursively ingest all files in directory
        Returns dict of file types and chunk counts
        """
        if file_patterns is None:
            file_patterns = ["*.txt", "*.md", "*.pdf"]
        
        stats = {}
        path = Path(directory)
        
        for pattern in file_patterns:
            for file_path in path.rglob(pattern):
                ext = file_path.suffix.lower()
                
                try:
                    if ext == '.pdf':
                        count = self.ingest_pdf(str(file_path))
                    else:
                        count = self.ingest_text_file(str(file_path))
                    
                    stats[str(file_path)] = count
                except Exception as e:
                    logger.error(f"Failed to ingest {file_path}: {e}")
        
        return stats
    
    def search(self, query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Document]:
        """
        Search knowledge base
        Returns top k relevant documents
        """
        if filter_dict:
            results = self.vector_store.similarity_search(query, k=k, filter=filter_dict)
        else:
            results = self.vector_store.similarity_search(query, k=k)
        
        return results
    
    def get_relevant_context(self, query: str, max_tokens: int = 4000) -> str:
        """
        Get relevant context for a query, limited by token count
        """
        docs = self.search(query, k=10)
        
        context_parts = []
        total_length = 0
        
        for doc in docs:
            content = doc.page_content
            if total_length + len(content) > max_tokens * 4:  # Rough estimate
                break
            context_parts.append(f"[Source: {doc.metadata.get('source', 'unknown')}]\n{content}")
            total_length += len(content)
        
        return "\n\n---\n\n".join(context_parts)
