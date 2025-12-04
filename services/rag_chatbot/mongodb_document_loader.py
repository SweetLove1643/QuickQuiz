#!/usr/bin/env python3
"""
MongoDB Document Loader for Vector Database

Load documents từ MongoDB và prepare cho FAISS vectorization.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from mongodb_adapter import MongoDBAdapter, get_mongodb_adapter
from schemas import SummaryDocument, DocumentChunk

logger = logging.getLogger(__name__)


class MongoDBDocumentLoader:
    """Load documents từ MongoDB cho vector database."""

    def __init__(self, mongodb_adapter: Optional[MongoDBAdapter] = None):
        """
        Initialize document loader.

        Args:
            mongodb_adapter: MongoDB adapter instance
        """
        self.mongodb_adapter = mongodb_adapter or get_mongodb_adapter()
        self.is_connected = False

    def initialize(self) -> None:
        """Initialize MongoDB connection."""
        try:
            self.mongodb_adapter.connect_sync()
            self.is_connected = True
            logger.info("✅ MongoDB Document Loader initialized")

            # Log collection stats
            stats = self.mongodb_adapter.get_collection_stats()
            logger.info(f"📊 MongoDB Stats: {stats}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB loader: {e}")
            raise

    def load_all_documents(
        self,
        topic_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Load all documents từ MongoDB.

        Args:
            topic_filter: Filter by topic
            category_filter: Filter by category
            limit: Maximum documents to load

        Returns:
            List of processed documents
        """
        if not self.is_connected:
            self.initialize()

        try:
            # Get documents from MongoDB
            raw_docs = self.mongodb_adapter.get_all_documents(
                topic_filter=topic_filter, category_filter=category_filter, limit=limit
            )

            # Process documents for vector store
            processed_docs = []

            for raw_doc in raw_docs:
                processed_doc = self._process_document(raw_doc)
                if processed_doc:
                    processed_docs.append(processed_doc)

            logger.info(f"📄 Loaded {len(processed_docs)} documents from MongoDB")
            return processed_docs

        except Exception as e:
            logger.error(f"❌ Error loading documents: {e}")
            raise

    def _process_document(self, raw_doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process raw MongoDB document cho vector store.
        Now handles the new structure from MongoDB adapter.

        Args:
            raw_doc: Raw document from MongoDB (already processed by adapter)

        Returns:
            Processed document hoặc None nếu invalid
        """
        try:
            # Extract fields (adapter already processed these)
            doc_id = raw_doc.get("_id") or "unknown"
            content = raw_doc.get("content", "")
            topic = raw_doc.get("topic", "General")
            category = raw_doc.get("category", "Uncategorized")
            title = raw_doc.get("title", "")
            source = raw_doc.get("source", "mongodb")
            user_email = raw_doc.get("user_email", "unknown")

            # Validate content
            if not content or len(content.strip()) < 10:
                logger.warning(f"⚠️ Skipping document {doc_id}: content too short")
                return None

            # Create processed document for vector store
            processed_doc = {
                "id": str(doc_id),
                "content": content.strip(),
                "topic": topic,
                "category": category,
                "metadata": {
                    "title": title,
                    "source": source,
                    "user_email": user_email,
                    "content_length": len(content),
                    "processed_at": datetime.now().isoformat(),
                    # Preserve original metadata
                    **raw_doc.get("metadata", {}),
                },
            }

            logger.debug(
                f"✅ Processed document {doc_id}: {title} ({topic}/{category})"
            )
            return processed_doc

        except Exception as e:
            logger.error(f"❌ Error processing document: {e}")
            return None

    def load_documents_by_topic(
        self, topic: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Load documents filtered by topic."""
        return self.load_all_documents(topic_filter=topic, limit=limit)

    def load_documents_by_category(
        self, category: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Load documents filtered by category."""
        return self.load_all_documents(category_filter=category, limit=limit)

    def get_available_topics(self) -> List[str]:
        """Get list of available topics."""
        if not self.is_connected:
            self.initialize()

        try:
            stats = self.mongodb_adapter.get_collection_stats()
            return stats.get("topics", [])
        except Exception as e:
            logger.error(f"❌ Error getting topics: {e}")
            return []

    def get_available_categories(self) -> List[str]:
        """Get list of available categories."""
        if not self.is_connected:
            self.initialize()

        try:
            stats = self.mongodb_adapter.get_collection_stats()
            return stats.get("categories", [])
        except Exception as e:
            logger.error(f"❌ Error getting categories: {e}")
            return []

    def get_loader_stats(self) -> Dict[str, Any]:
        """Get loader statistics."""
        if not self.is_connected:
            self.initialize()

        try:
            mongodb_stats = self.mongodb_adapter.get_collection_stats()

            loader_stats = {
                "loader_status": "connected" if self.is_connected else "disconnected",
                "mongodb_stats": mongodb_stats,
                "available_topics": len(mongodb_stats.get("topics", [])),
                "available_categories": len(mongodb_stats.get("categories", [])),
                "total_documents": mongodb_stats.get("total_documents", 0),
            }

            return loader_stats

        except Exception as e:
            logger.error(f"❌ Error getting loader stats: {e}")
            return {"error": str(e)}

    def close(self) -> None:
        """Close MongoDB connections."""
        try:
            self.mongodb_adapter.close_connections()
            self.is_connected = False
            logger.info("🔒 MongoDB Document Loader closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing loader: {e}")


def get_mongodb_document_loader() -> MongoDBDocumentLoader:
    """Factory function to create MongoDB document loader."""
    return MongoDBDocumentLoader()


# Test function
def test_mongodb_document_loader():
    """Test MongoDB document loader."""
    print("🧪 Testing MongoDB Document Loader...")

    loader = get_mongodb_document_loader()

    try:
        # Initialize loader
        loader.initialize()

        # Get stats
        stats = loader.get_loader_stats()
        print(f"📊 Loader Stats: {stats}")

        # Load sample documents
        docs = loader.load_all_documents(limit=5)
        print(f"📄 Loaded Documents: {len(docs)}")

        for i, doc in enumerate(docs[:2]):
            print(f"  Doc {i+1}: {doc['id']} - {doc['topic']}/{doc['category']}")
            print(f"           Content: {doc['content'][:100]}...")

        # Test topic filtering
        topics = loader.get_available_topics()
        if topics:
            first_topic = topics[0]
            topic_docs = loader.load_documents_by_topic(first_topic, limit=3)
            print(f"📋 Topic '{first_topic}': {len(topic_docs)} documents")

        print("✅ MongoDB Document Loader test successful!")

    except Exception as e:
        print(f"❌ MongoDB Document Loader test failed: {e}")

    finally:
        loader.close()


if __name__ == "__main__":
    test_mongodb_document_loader()
