"""
Document Store - Handles PDF and document ingestion for agent context
Supports: PDF, TXT, Markdown, DOCX
Uses ChromaDB for vector storage and semantic search

This module allows agents to query internal company documents alongside
online scraped data for comprehensive analysis.
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

# PDF handling
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logger.warning("PyMuPDF not installed. Run: uv pip install pymupdf")

# Vector store
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_SUPPORT = True
except ImportError:
    CHROMA_SUPPORT = False
    logger.warning("ChromaDB not installed. Run: uv pip install chromadb")

# Text splitting
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    LANGCHAIN_SUPPORT = True
except ImportError:
    LANGCHAIN_SUPPORT = False


class DocumentStore:
    """
    Manages internal company documents for agent context.
    
    Features:
    - PDF/TXT/MD ingestion
    - Chunking with overlap for better context
    - Vector embeddings via ChromaDB
    - Semantic search for relevant context
    - Document metadata tracking
    - Category-based organization (kubernetes, os, general)
    
    Usage:
        store = DocumentStore()
        store.ingest_document("policy.pdf", category="kubernetes")
        context = store.get_context_for_agent("kubernetes", "container runtime version")
    """
    
    def __init__(self, 
                 store_path: str = None,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize the document store.
        
        Args:
            store_path: Path to store documents and vectors
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks for context continuity
        """
        # Default path relative to project
        if store_path is None:
            store_path = Path(__file__).parent.parent / "document_store"
        
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Document registry (tracks all ingested documents)
        self.registry_path = self.store_path / "document_registry.json"
        self.registry = self._load_registry()
        
        # Initialize ChromaDB for vector storage
        if CHROMA_SUPPORT:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.store_path / "chroma_db")
            )
            # Create collections for different document types
            self.collections = {
                "kubernetes": self.chroma_client.get_or_create_collection(
                    name="kubernetes_docs",
                    metadata={"description": "Kubernetes-related internal documents"}
                ),
                "os": self.chroma_client.get_or_create_collection(
                    name="os_docs", 
                    metadata={"description": "OS-related internal documents"}
                ),
                "general": self.chroma_client.get_or_create_collection(
                    name="general_docs",
                    metadata={"description": "General internal documents"}
                )
            }
        else:
            self.chroma_client = None
            self.collections = {}
        
        logger.info(f"Document Store initialized at: {self.store_path}")
        logger.info(f"PDF Support: {PDF_SUPPORT}, Vector Store: {CHROMA_SUPPORT}")
    
    def _load_registry(self) -> Dict:
        """Load document registry from disk"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
        return {"documents": [], "last_updated": None}
    
    def _save_registry(self):
        """Save document registry to disk"""
        self.registry["last_updated"] = datetime.now().isoformat()
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file for deduplication"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    
    def _extract_pdf_text(self, file_path: Path) -> Dict[str, Any]:
        """Extract text and metadata from PDF using PyMuPDF"""
        if not PDF_SUPPORT:
            raise ImportError("PyMuPDF not installed. Run: uv pip install pymupdf")
        
        doc = fitz.open(file_path)
        
        # Extract metadata
        metadata = {
            "title": doc.metadata.get("title", file_path.stem),
            "author": doc.metadata.get("author", "Unknown"),
            "pages": len(doc),
            "creation_date": doc.metadata.get("creationDate", ""),
        }
        
        # Extract text page by page with page numbers
        pages = []
        full_text = ""
        
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            pages.append({
                "page": page_num,
                "text": text,
                "char_count": len(text)
            })
            full_text += f"\n\n[Page {page_num}]\n{text}"
        
        doc.close()
        
        return {
            "text": full_text,
            "pages": pages,
            "metadata": metadata
        }
    
    def _extract_text_file(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from TXT/MD files"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        return {
            "text": text,
            "pages": [{"page": 1, "text": text, "char_count": len(text)}],
            "metadata": {
                "title": file_path.stem,
                "author": "Unknown",
                "pages": 1
            }
        }
    
    def _chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """Split text into chunks with overlap for better context retrieval"""
        if LANGCHAIN_SUPPORT:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = splitter.split_text(text)
        else:
            # Simple chunking fallback
            chunks = []
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunk = text[i:i + self.chunk_size]
                if chunk.strip():
                    chunks.append(chunk)
        
        return [
            {
                "id": f"{metadata.get('doc_id', 'doc')}_{i}",
                "text": chunk,
                "metadata": {
                    **metadata,
                    "chunk_index": i,
                    "chunk_count": len(chunks)
                }
            }
            for i, chunk in enumerate(chunks)
        ]
    
    def ingest_document(self, 
                       file_path: str,
                       category: str = "general",
                       tags: List[str] = None,
                       description: str = None) -> Dict[str, Any]:
        """
        Ingest a document into the store for agent context.
        
        Args:
            file_path: Path to the document (PDF, TXT, MD)
            category: Document category - "kubernetes", "os", or "general"
            tags: List of tags for filtering (e.g., ["policy", "versions"])
            description: Human-readable description of the document
            
        Returns:
            Dict with ingestion result including doc_id and chunk count
            
        Example:
            result = store.ingest_document(
                "docs/k8s-policy.pdf",
                category="kubernetes",
                tags=["policy", "versions"],
                description="Company K8s version policy"
            )
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Check for duplicates using file hash
        file_hash = self._get_file_hash(file_path)
        for doc in self.registry["documents"]:
            if doc["hash"] == file_hash:
                logger.warning(f"Document already ingested: {doc['filename']}")
                return {"status": "duplicate", "doc_id": doc["id"]}
        
        # Extract text based on file type
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            if not PDF_SUPPORT:
                raise ImportError("PDF support requires: uv pip install pymupdf")
            extraction = self._extract_pdf_text(file_path)
        elif suffix in [".txt", ".md", ".markdown"]:
            extraction = self._extract_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}. Supported: .pdf, .txt, .md")
        
        # Generate unique document ID
        doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.stem[:20]}"
        
        # Create document metadata
        doc_metadata = {
            "doc_id": doc_id,
            "filename": file_path.name,
            "category": category,
            "tags": tags or [],
            "description": description or extraction["metadata"].get("title", ""),
            "source_type": "internal_document",
            "file_type": suffix,
            "ingested_at": datetime.now().isoformat()
        }
        
        # Chunk the document for vector storage
        chunks = self._chunk_text(extraction["text"], doc_metadata)
        
        # Store chunks in ChromaDB
        if CHROMA_SUPPORT and category in self.collections:
            collection = self.collections[category]
            
            # Add chunks to collection
            collection.add(
                ids=[c["id"] for c in chunks],
                documents=[c["text"] for c in chunks],
                metadatas=[{k: str(v) if isinstance(v, list) else v 
                           for k, v in c["metadata"].items()} for c in chunks]
            )
            
            logger.info(f"Indexed {len(chunks)} chunks in '{category}' collection")
        
        # Update registry
        registry_entry = {
            "id": doc_id,
            "filename": file_path.name,
            "path": str(file_path.absolute()),
            "hash": file_hash,
            "category": category,
            "tags": tags or [],
            "description": description,
            "chunk_count": len(chunks),
            "total_chars": len(extraction["text"]),
            "pages": extraction["metadata"].get("pages", 1),
            "ingested_at": datetime.now().isoformat()
        }
        self.registry["documents"].append(registry_entry)
        self._save_registry()
        
        logger.info(f"Ingested: {file_path.name} | Category: {category} | Chunks: {len(chunks)}")
        
        return {
            "status": "success",
            "doc_id": doc_id,
            "chunks": len(chunks),
            "category": category,
            "chars": len(extraction["text"])
        }
    
    def search(self, 
               query: str, 
               category: str = None,
               n_results: int = 5,
               tags: List[str] = None) -> List[Dict]:
        """
        Search for relevant document chunks using semantic search.
        
        Args:
            query: Search query (natural language)
            category: Filter by category (kubernetes, os, general) or None for all
            n_results: Maximum number of results to return
            tags: Filter by tags (optional)
            
        Returns:
            List of relevant chunks with metadata and relevance scores
        """
        if not CHROMA_SUPPORT:
            logger.warning("Vector search not available without ChromaDB")
            return []
        
        results = []
        
        # Search specific category or all categories
        categories_to_search = [category] if category else list(self.collections.keys())
        
        for cat in categories_to_search:
            if cat not in self.collections:
                continue
                
            collection = self.collections[cat]
            
            try:
                search_results = collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
                
                # Format results
                if search_results["documents"] and search_results["documents"][0]:
                    for i, doc in enumerate(search_results["documents"][0]):
                        meta = search_results["metadatas"][0][i] if search_results["metadatas"] else {}
                        distance = search_results["distances"][0][i] if search_results.get("distances") else 0
                        
                        results.append({
                            "text": doc,
                            "category": cat,
                            "metadata": meta,
                            "relevance_score": 1 - (distance / 2),  # Convert distance to score
                            "source": meta.get("filename", "unknown")
                        })
            except Exception as e:
                logger.error(f"Search error in {cat}: {e}")
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results[:n_results]
    
    def get_context_for_agent(self, 
                              agent_type: str,
                              query: str,
                              max_chars: int = 8000) -> Dict[str, Any]:
        """
        Get relevant context from internal documents for a specific agent.
        
        This is the main method agents should use to get internal document context.
        
        Args:
            agent_type: Type of agent ("kubernetes", "os", or agent name like "kubernetes-agent")
            query: Query describing what context is needed
            max_chars: Maximum characters to return (to fit in LLM context)
            
        Returns:
            Dict with:
            - context: Combined text from relevant documents
            - sources: List of source document names
            - chunks_used: Number of chunks included
            - total_chars: Character count
            
        Example:
            context = store.get_context_for_agent(
                agent_type="kubernetes",
                query="container runtime version requirements",
                max_chars=10000
            )
        """
        # Map agent type to category
        category_map = {
            "kubernetes": "kubernetes",
            "os": "os",
            "kubernetes-agent": "kubernetes",
            "os-agent": "os"
        }
        
        category = category_map.get(agent_type, "general")
        
        # Search for relevant chunks in the category
        results = self.search(query, category=category, n_results=10)
        
        # Also search general docs for additional context
        general_results = self.search(query, category="general", n_results=5)
        results.extend(general_results)
        
        # Sort by relevance and deduplicate
        seen = set()
        unique_results = []
        for r in sorted(results, key=lambda x: x["relevance_score"], reverse=True):
            text_hash = hash(r["text"][:100])
            if text_hash not in seen:
                seen.add(text_hash)
                unique_results.append(r)
        
        # Build context string within character limit
        context_parts = []
        total_chars = 0
        sources = []
        
        for result in unique_results:
            if total_chars + len(result["text"]) > max_chars:
                break
            
            context_parts.append(f"[Source: {result['source']}]\n{result['text']}")
            total_chars += len(result["text"])
            
            if result["source"] not in sources:
                sources.append(result["source"])
        
        context_text = "\n\n---\n\n".join(context_parts)
        
        return {
            "context": context_text,
            "sources": sources,
            "chunks_used": len(context_parts),
            "total_chars": total_chars,
            "category": category
        }
    
    def list_documents(self, category: str = None) -> List[Dict]:
        """
        List all ingested documents.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of document metadata dicts
        """
        docs = self.registry["documents"]
        if category:
            docs = [d for d in docs if d["category"] == category]
        return docs
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a document from the store.
        
        Args:
            doc_id: Document ID to remove
            
        Returns:
            True if removed, False if not found
        """
        # Find document
        doc = None
        for d in self.registry["documents"]:
            if d["id"] == doc_id:
                doc = d
                break
        
        if not doc:
            return False
        
        # Remove from ChromaDB
        if CHROMA_SUPPORT and doc["category"] in self.collections:
            collection = self.collections[doc["category"]]
            # Get all chunk IDs for this document
            chunk_ids = [f"{doc_id}_{i}" for i in range(doc["chunk_count"])]
            try:
                collection.delete(ids=chunk_ids)
            except Exception as e:
                logger.error(f"Failed to delete from ChromaDB: {e}")
        
        # Remove from registry
        self.registry["documents"] = [d for d in self.registry["documents"] if d["id"] != doc_id]
        self._save_registry()
        
        logger.info(f"Removed document: {doc['filename']}")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get document store statistics"""
        docs = self.registry["documents"]
        
        stats = {
            "total_documents": len(docs),
            "total_chunks": sum(d.get("chunk_count", 0) for d in docs),
            "total_chars": sum(d.get("total_chars", 0) for d in docs),
            "by_category": {}
        }
        
        for doc in docs:
            cat = doc.get("category", "general")
            if cat not in stats["by_category"]:
                stats["by_category"][cat] = {"count": 0, "chunks": 0}
            stats["by_category"][cat]["count"] += 1
            stats["by_category"][cat]["chunks"] += doc.get("chunk_count", 0)
        
        return stats


# Singleton instance for easy access across modules
_document_store_instance = None

def get_document_store(store_path: str = None) -> DocumentStore:
    """
    Get or create the document store singleton.
    
    Args:
        store_path: Optional custom store path (only used on first call)
        
    Returns:
        DocumentStore instance
    """
    global _document_store_instance
    if _document_store_instance is None:
        _document_store_instance = DocumentStore(store_path=store_path)
    return _document_store_instance
