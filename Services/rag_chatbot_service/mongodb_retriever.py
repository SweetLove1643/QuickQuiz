#!/usr/bin/env python3
"""
MongoDB-Integrated Document Retriever

Enhanced retriever sử dụng MongoDB làm data source cho vector database.
"""

import os
import logging
from typing import List, Optional

from vector_store_langchain import LangChainVectorStore
from schemas import RetrievalConfig, RetrievedDocument
from mongodb_document_loader import MongoDBDocumentLoader, get_mongodb_document_loader

logger = logging.getLogger(__name__)


class MongoDBDocumentRetriever:
    """
    MongoDB-integrated document retriever với LangChain FAISS.

    Features:
    - Load documents từ MongoDB thay vì mock JSON
    - Persistent FAISS vector store
    - Flexible filtering by topic/category
    - Auto-refresh when MongoDB data changes
    """

    def __init__(
        self,
        mongodb_loader: Optional[MongoDBDocumentLoader] = None,
        persist_directory: Optional[str] = None,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        auto_refresh: bool = False,
    ):
        """
        Initialize MongoDB document retriever.

        Args:
            mongodb_loader: MongoDB document loader instance
            persist_directory: Directory to persist FAISS index
            embedding_model: HuggingFace embedding model name
            auto_refresh: Auto refresh vector store when MongoDB changes
        """
        self.mongodb_loader = mongodb_loader or get_mongodb_document_loader()
        self.persist_directory = persist_directory or self._get_default_persist_dir()
        self.embedding_model = embedding_model
        self.auto_refresh = auto_refresh

        # LangChain vector store instance
        self.vector_store = LangChainVectorStore(
            embedding_model=embedding_model, persist_directory=self.persist_directory
        )

        self.is_initialized = False
        self._last_document_count = 0

    def _get_default_persist_dir(self) -> str:
        """Get default persist directory."""
        current_dir = os.path.dirname(__file__)
        return os.path.join(current_dir, "faiss_db_mongodb")

    def initialize(self, force_rebuild: bool = False) -> None:
        """
        Initialize retriever với MongoDB data.

        Args:
            force_rebuild: Force rebuild FAISS index from MongoDB
        """
        logger.info("Initializing MongoDB Document Retriever...")

        try:
            # Initialize MongoDB loader
            self.mongodb_loader.initialize()

            # Check if need to rebuild
            should_rebuild = force_rebuild or self._should_rebuild_index()

            if should_rebuild:
                logger.info("🔄 Building vector store from MongoDB data...")
                self._build_vector_store_from_mongodb()
            else:
                logger.info("📁 Loading existing vector store...")
                self._load_existing_vector_store()

            self.is_initialized = True

            # Log stats
            stats = self.get_stats()
            logger.info(f"✅ MongoDB Retriever initialized - {stats}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB retriever: {e}")
            raise

    def _should_rebuild_index(self) -> bool:
        """Check if should rebuild FAISS index."""
        try:
            # Check if persist directory exists
            if not os.path.exists(self.persist_directory):
                logger.info("📁 Persist directory not found - will build new index")
                return True

            # Check MongoDB document count
            loader_stats = self.mongodb_loader.get_loader_stats()
            current_doc_count = loader_stats.get("total_documents", 0)

            # If document count changed significantly, rebuild
            if abs(current_doc_count - self._last_document_count) > 5:
                logger.info(
                    f"📊 Document count changed: {self._last_document_count} → {current_doc_count}"
                )
                return True

            return False

        except Exception as e:
            logger.warning(f"⚠️ Error checking rebuild need: {e}")
            return True

    def _build_vector_store_from_mongodb(self) -> None:
        """Build vector store từ MongoDB documents."""
        try:
            # Load documents from MongoDB
            logger.info("📥 Loading documents from MongoDB...")
            documents = self.mongodb_loader.load_all_documents()

            if not documents:
                raise ValueError("No documents loaded from MongoDB")

            # Convert to LangChain format
            langchain_docs = []
            for doc in documents:
                langchain_doc = {
                    "content": doc["content"],
                    "metadata": {
                        "id": doc["id"],
                        "topic": doc["topic"],
                        "category": doc["category"],
                        **doc.get("metadata", {}),
                    },
                }
                langchain_docs.append(langchain_doc)

            logger.info(f"📄 Processing {len(langchain_docs)} documents...")

            # Build vector store
            self.vector_store.build_from_documents(langchain_docs)

            # Save document count for future checks
            self._last_document_count = len(documents)

            logger.info(
                f"✅ Vector store built from {len(documents)} MongoDB documents"
            )

        except Exception as e:
            logger.error(f"❌ Error building vector store from MongoDB: {e}")
            raise

    def _load_existing_vector_store(self) -> None:
        """Load existing vector store."""
        try:
            self.vector_store.load_from_disk()

            # Update document count
            loader_stats = self.mongodb_loader.get_loader_stats()
            self._last_document_count = loader_stats.get("total_documents", 0)

            logger.info("✅ Loaded existing vector store")

        except Exception as e:
            logger.warning(f"⚠️ Failed to load existing store: {e}")
            # Fallback to rebuild
            self._build_vector_store_from_mongodb()

    def retrieve_documents(
        self, query: str, config: RetrievalConfig
    ) -> List[RetrievedDocument]:
        """
        Retrieve documents using vector similarity search.

        Args:
            query: Search query
            config: Retrieval configuration

        Returns:
            List of retrieved documents với similarity scores
        """
        if not self.is_initialized:
            self.initialize()

        try:
            # Check for auto-refresh
            if self.auto_refresh and self._should_rebuild_index():
                logger.info("🔄 Auto-refreshing vector store...")
                self._build_vector_store_from_mongodb()

            # Perform vector search
            results = self.vector_store.search_documents(
                query=query,
                top_k=config.top_k,
                similarity_threshold=config.similarity_threshold,
                topic_filter=config.topic_filter,
            )

            # Convert to RetrievedDocument format
            retrieved_docs = []
            for result in results:
                retrieved_doc = RetrievedDocument(
                    document_id=result.get("id", "unknown"),
                    chunk_id=f"{result.get('id', 'unknown')}_chunk_{len(retrieved_docs)}",
                    content=result.get("chunk_text", result.get("content", "")),
                    topic=result.get("topic", "Unknown"),
                    category=result.get("category", "Unknown"),
                    similarity_score=result.get("similarity_score", 0.0),
                    tags=result.get("tags", []),
                )
                retrieved_docs.append(retrieved_doc)

            logger.info(
                f"📊 Retrieved {len(retrieved_docs)} documents for query: '{query[:50]}...'"
            )
            return retrieved_docs

        except Exception as e:
            logger.error(f"❌ Error retrieving documents: {e}")
            return []

    def get_document_by_id(self, document_id: str) -> Optional[dict]:
        """Get document by ID từ MongoDB."""
        try:
            return self.mongodb_loader.mongodb_adapter.get_document_by_id(document_id)
        except Exception as e:
            logger.error(f"❌ Error getting document {document_id}: {e}")
            return None

    def list_all_topics(self) -> List[str]:
        """Get all available topics từ MongoDB."""
        try:
            return self.mongodb_loader.get_available_topics()
        except Exception as e:
            logger.error(f"❌ Error listing topics: {e}")
            return []

    def list_all_categories(self) -> List[str]:
        """Get all available categories từ MongoDB."""
        try:
            return self.mongodb_loader.get_available_categories()
        except Exception as e:
            logger.error(f"❌ Error listing categories: {e}")
            return []

    def rebuild_index(self) -> None:
        """Force rebuild FAISS index từ MongoDB."""
        logger.info("🔄 Force rebuilding index from MongoDB...")
        self._build_vector_store_from_mongodb()

    def clear_cache(self) -> None:
        """Clear vector store cache."""
        try:
            self.vector_store.clear_cache()
            logger.info("🗑️ Vector store cache cleared")
        except Exception as e:
            logger.warning(f"⚠️ Error clearing cache: {e}")

    def get_stats(self) -> dict:
        """Get comprehensive retriever statistics."""
        try:
            vector_stats = self.vector_store.get_stats()
            loader_stats = self.mongodb_loader.get_loader_stats()

            return {
                "retriever_type": "mongodb_integrated",
                "is_initialized": self.is_initialized,
                "vector_store": vector_stats,
                "mongodb_loader": loader_stats,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embedding_model,
                "auto_refresh": self.auto_refresh,
                "last_document_count": self._last_document_count,
            }

        except Exception as e:
            return {"error": str(e)}

    def close(self) -> None:
        """Close all connections."""
        try:
            self.mongodb_loader.close()
            # Vector store doesn't need explicit closing
            logger.info("🔒 MongoDB Document Retriever closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing retriever: {e}")


# Factory function
def get_mongodb_document_retriever(**kwargs) -> MongoDBDocumentRetriever:
    """Factory function to create MongoDB document retriever."""
    return MongoDBDocumentRetriever(**kwargs)


# Test function
def test_mongodb_retriever():
    """Test MongoDB document retriever."""
    print("🧪 Testing MongoDB Document Retriever...")

    retriever = get_mongodb_document_retriever()

    try:
        # Initialize
        retriever.initialize()

        # Test search
        from schemas import RetrievalConfig

        config = RetrievalConfig(top_k=3, similarity_threshold=0.3)

        results = retriever.retrieve_documents("Python programming", config)
        print(f"🔍 Search Results: {len(results)} documents found")

        for i, doc in enumerate(results):
            print(
                f"  {i+1}. {doc.topic}/{doc.category} (score: {doc.similarity_score:.3f})"
            )
            print(f"      {doc.content[:100]}...")

        # Test stats
        stats = retriever.get_stats()
        print(f"📊 Retriever Stats: {stats}")

        print("✅ MongoDB Document Retriever test successful!")

    except Exception as e:
        print(f"❌ MongoDB Document Retriever test failed: {e}")

    finally:
        retriever.close()


if __name__ == "__main__":
    test_mongodb_retriever()
