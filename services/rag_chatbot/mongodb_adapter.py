#!/usr/bin/env python3
"""
MongoDB Adapter for RAG Chatbot

Connect MongoDB và query documents để xây dựng vector database.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

import pymongo
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from schemas import SummaryDocument

logger = logging.getLogger(__name__)


class MongoDBAdapter:
    """MongoDB adapter cho RAG system."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        database_name: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        """
        Initialize MongoDB adapter.

        Args:
            connection_string: MongoDB connection string
            database_name: Database name
            collection_name: Collection name for documents
        """
        # Load environment variables if not already loaded
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        # Get credentials from environment
        username = os.getenv("MONGO_DB_USERNAME")
        password = os.getenv("MONGO_DB_PASSWORD")

        # Debug logging
        logger.debug(f"Username from env: {username}")
        logger.debug(f"Password from env: {'***' if password else 'None'}")

        # Build connection string properly
        if connection_string:
            # Use provided connection string and expand it
            self.connection_string = self._expand_connection_string(
                connection_string, username, password
            )
        else:
            # Build connection string from environment template
            connection_template = os.getenv(
                "MONGODB_CONNECTION_STRING", "mongodb://localhost:27017"
            )

            # Debug logging
            logger.debug(f"Connection template from env: {connection_template}")

            # Check if template contains placeholders that need expansion
            if (
                "${MONGO_DB_USERNAME}" in connection_template
                or "${MONGO_DB_PASSWORD}" in connection_template
            ):
                self.connection_string = self._expand_connection_string(
                    connection_template, username, password
                )
            else:
                # Template might already be expanded by dotenv, build manually
                if username and password:
                    # Build connection string manually for MongoDB Atlas
                    cluster_url = "hackathon.n5sib2v.mongodb.net"
                    database = "hackathon"
                    self.connection_string = f"mongodb+srv://{username}:{password}@{cluster_url}/{database}?retryWrites=true&w=majority&appName=Hackathon"
                    logger.info(
                        f"🔗 Built MongoDB connection: {self._mask_password(self.connection_string)}"
                    )
                else:
                    # Fallback to template as-is
                    self.connection_string = connection_template

        self.database_name = database_name or os.getenv(
            "MONGODB_DATABASE_NAME", "hackathon"
        )
        self.collection_name = collection_name or os.getenv(
            "MONGODB_COLLECTION_NAME", "quiz_data"
        )

        # Sync client for initialization
        self.sync_client: Optional[MongoClient] = None
        self.sync_db = None
        self.sync_collection = None

        # Async client for async operations
        self.async_client: Optional[AsyncIOMotorClient] = None
        self.async_db = None
        self.async_collection = None

    def _expand_connection_string(
        self, template: str, username: Optional[str], password: Optional[str]
    ) -> str:
        """
        Expand environment variables in connection string.

        Args:
            template: Connection string template with ${VAR} placeholders
            username: MongoDB username
            password: MongoDB password

        Returns:
            Expanded connection string
        """
        try:
            # Replace template variables
            connection_string = template

            # Check for missing credentials
            if "${MONGO_DB_USERNAME}" in connection_string:
                if not username:
                    raise ValueError(
                        "MONGO_DB_USERNAME environment variable is missing or empty"
                    )
                connection_string = connection_string.replace(
                    "${MONGO_DB_USERNAME}", username
                )

            if "${MONGO_DB_PASSWORD}" in connection_string:
                if not password:
                    raise ValueError(
                        "MONGO_DB_PASSWORD environment variable is missing or empty"
                    )
                connection_string = connection_string.replace(
                    "${MONGO_DB_PASSWORD}", password
                )

            logger.info(
                f"🔗 MongoDB connection: {self._mask_password(connection_string)}"
            )
            return connection_string

        except Exception as e:
            logger.error(f"❌ Error expanding connection string: {e}")
            raise

    def _mask_password(self, connection_string: str) -> str:
        """Mask password in connection string for logging."""
        try:
            if "://" in connection_string and "@" in connection_string:
                # Extract and mask password part
                protocol_part, rest = connection_string.split("://", 1)
                if "@" in rest:
                    auth_part, server_part = rest.split("@", 1)
                    if ":" in auth_part:
                        username, _ = auth_part.split(":", 1)
                        return f"{protocol_part}://{username}:***@{server_part}"
            return connection_string
        except:
            return "***masked***"

    def connect_sync(self) -> None:
        """Connect to MongoDB using sync client."""
        try:
            self.sync_client = MongoClient(self.connection_string)

            # Test connection
            self.sync_client.admin.command("ping")
            logger.info("✅ MongoDB sync connection successful")

            # Setup database and collection
            self.sync_db = self.sync_client[self.database_name]
            self.sync_collection = self.sync_db[self.collection_name]

            # Create indexes for better performance
            self._create_indexes_sync()

        except Exception as e:
            logger.error(f"❌ MongoDB sync connection failed: {e}")
            raise

    async def connect_async(self) -> None:
        """Connect to MongoDB using async client."""
        try:
            self.async_client = AsyncIOMotorClient(self.connection_string)

            # Test connection
            await self.async_client.admin.command("ping")
            logger.info("✅ MongoDB async connection successful")

            # Setup database and collection
            self.async_db = self.async_client[self.database_name]
            self.async_collection = self.async_db[self.collection_name]

        except Exception as e:
            logger.error(f"❌ MongoDB async connection failed: {e}")
            raise

    def _create_indexes_sync(self) -> None:
        """Create indexes for better query performance."""
        try:
            # Index on topic for filtering
            self.sync_collection.create_index("topic")

            # Index on category for filtering
            self.sync_collection.create_index("category")

            # Index on user_id for user filtering
            self.sync_collection.create_index("user_id")

            # Text search index on content
            self.sync_collection.create_index([("content", "text"), ("topic", "text")])

            # Compound index for common queries
            self.sync_collection.create_index([("topic", 1), ("category", 1)])

            logger.info("✅ MongoDB indexes created successfully")

        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")

    def get_all_documents(
        self,
        topic_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        user_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all documents from MongoDB với filtering options.
        Now extracts summaries from multiple collections.

        Args:
            topic_filter: Filter by topic
            category_filter: Filter by category
            user_filter: Filter by user_id
            limit: Maximum number of documents

        Returns:
            List of processed documents for RAG
        """
        if self.sync_client is None:
            raise RuntimeError("MongoDB not connected. Call connect_sync() first.")

        try:
            documents = []

            # 1. Get summaries from users collection
            logger.info("📝 Extracting summaries from users collection...")
            users_collection = self.sync_db["users"]
            users_with_summaries = users_collection.find(
                {"summaries": {"$exists": True, "$ne": []}}
            )

            for user in users_with_summaries:
                summaries = user.get("summaries", [])
                user_email = user.get("email", "unknown")

                for i, summary in enumerate(summaries):
                    if isinstance(summary, str) and summary.strip():
                        doc = {
                            "_id": f"user_summary_{user['_id']}_{i}",
                            "content": summary.strip(),
                            "title": f"Summary by {user_email}",
                            "topic": "Network Layered Model",  # Based on content analysis
                            "category": "summary",
                            "source": "users",
                            "user_email": user_email,
                            "metadata": {
                                "type": "user_summary",
                                "user_id": str(user["_id"]),
                                "summary_index": i,
                            },
                        }
                        documents.append(doc)

            # 2. Get content from WH_Note collection
            logger.info("📚 Extracting content from WH_Note collection...")
            notes_collection = self.sync_db["WH_Note"]
            notes = notes_collection.find({})

            for note in notes:
                title = note.get("title", "")
                content = note.get("content", "")

                if content and isinstance(content, str) and len(content.strip()) > 10:
                    doc = {
                        "_id": f"note_{note['_id']}",
                        "content": content.strip(),
                        "title": title or "Note",
                        "topic": title or "General Note",
                        "category": "note",
                        "source": "WH_Note",
                        "user_email": note.get("email", "unknown"),
                        "metadata": {
                            "type": "note",
                            "created_at": note.get("createdAt"),
                            "note_id": str(note["_id"]),
                        },
                    }
                    documents.append(doc)

            # 3. Get content from flash_cards collection
            logger.info("🎯 Extracting content from flash_cards collection...")
            cards_collection = self.sync_db["flash_cards"]
            flash_card_sets = cards_collection.find({})

            for card_set in flash_card_sets:
                cards = card_set.get("cards", [])
                user_email = card_set.get("email", "unknown")

                for i, card in enumerate(cards):
                    if isinstance(card, dict):
                        front = card.get("front", "").strip()
                        back = card.get("back", "").strip()

                        if front and back:
                            content = f"Q: {front}\nA: {back}"
                            doc = {
                                "_id": f"flashcard_{card_set['_id']}_{i}",
                                "content": content,
                                "title": f"Flashcard: {front[:50]}...",
                                "topic": "Study Cards",
                                "category": "flashcard",
                                "source": "flash_cards",
                                "user_email": user_email,
                                "metadata": {
                                    "type": "flashcard",
                                    "card_index": i,
                                    "set_id": str(card_set["_id"]),
                                },
                            }
                            documents.append(doc)

            # Apply filters if provided
            if topic_filter:
                documents = [
                    doc
                    for doc in documents
                    if topic_filter.lower() in doc.get("topic", "").lower()
                ]

            if category_filter:
                documents = [
                    doc
                    for doc in documents
                    if category_filter.lower() in doc.get("category", "").lower()
                ]

            if user_filter:
                documents = [
                    doc
                    for doc in documents
                    if user_filter.lower() in doc.get("user_email", "").lower()
                ]

            # Apply limit
            if limit:
                documents = documents[:limit]

            logger.info(
                f"📊 Retrieved {len(documents)} processed documents from MongoDB"
            )
            logger.info(
                f"   - Summaries: {len([d for d in documents if d['category'] == 'summary'])}"
            )
            logger.info(
                f"   - Notes: {len([d for d in documents if d['category'] == 'note'])}"
            )
            logger.info(
                f"   - Flashcards: {len([d for d in documents if d['category'] == 'flashcard'])}"
            )

            return documents

        except Exception as e:
            logger.error(f"❌ Error querying MongoDB: {e}")
            raise

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get single document by ID."""
        if self.sync_collection is None:
            raise RuntimeError("MongoDB not connected")

        try:
            # Try ObjectId first, then string ID
            query = {}
            if ObjectId.is_valid(document_id):
                query = {"$or": [{"_id": ObjectId(document_id)}, {"id": document_id}]}
            else:
                query = {"id": document_id}

            doc = self.sync_collection.find_one(query)

            if doc and "_id" in doc:
                doc["_id"] = str(doc["_id"])

            return doc

        except Exception as e:
            logger.error(f"❌ Error getting document {document_id}: {e}")
            return None

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if self.sync_collection is None:
            raise RuntimeError("MongoDB not connected")

        try:
            stats = {
                "total_documents": self.sync_collection.count_documents({}),
                "database_name": self.database_name,
                "collection_name": self.collection_name,
                "connection_string": (
                    self.connection_string.replace(
                        # Hide password in logs
                        self.connection_string.split("@")[0].split("//")[-1],
                        "***",
                    )
                    if "@" in self.connection_string
                    else self.connection_string
                ),
            }

            # Get unique topics and categories
            topics = self.sync_collection.distinct("topic")
            categories = self.sync_collection.distinct("category")

            stats.update(
                {
                    "unique_topics": len(topics),
                    "unique_categories": len(categories),
                    "topics": topics,
                    "categories": categories,
                }
            )

            return stats

        except Exception as e:
            logger.error(f"❌ Error getting collection stats: {e}")
            return {"error": str(e)}

    def close_connections(self) -> None:
        """Close all MongoDB connections."""
        try:
            if self.sync_client:
                self.sync_client.close()
                logger.info("🔒 MongoDB sync connection closed")

            if self.async_client:
                self.async_client.close()
                logger.info("🔒 MongoDB async connection closed")

        except Exception as e:
            logger.warning(f"⚠️ Error closing MongoDB connections: {e}")

    # Async methods for future use
    async def get_all_documents_async(
        self, topic_filter: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Async version of get_all_documents."""
        if self.async_collection is None:
            await self.connect_async()

        try:
            query_filter = {}
            if topic_filter:
                query_filter["topic"] = {"$regex": topic_filter, "$options": "i"}

            cursor = self.async_collection.find(query_filter)

            if limit:
                cursor = cursor.limit(limit)

            documents = await cursor.to_list(length=limit)

            # Convert ObjectId to string
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            return documents

        except Exception as e:
            logger.error(f"❌ Error in async query: {e}")
            raise


def get_mongodb_adapter() -> MongoDBAdapter:
    """Factory function để tạo MongoDB adapter."""
    return MongoDBAdapter()


# Test functions
def test_mongodb_connection():
    """Test MongoDB connection và basic operations."""
    print("🧪 Testing MongoDB Connection...")

    adapter = get_mongodb_adapter()

    try:
        # Test sync connection
        adapter.connect_sync()

        # Get stats
        stats = adapter.get_collection_stats()
        print(f"📊 Collection Stats: {stats}")

        # Get sample documents
        docs = adapter.get_all_documents(limit=5)
        print(f"📄 Sample Documents: {len(docs)} found")

        for i, doc in enumerate(docs[:2]):
            print(
                f"  Doc {i+1}: {doc.get('topic', 'Unknown')} - {doc.get('content', '')[:100]}..."
            )

        print("✅ MongoDB test successful!")

    except Exception as e:
        print(f"❌ MongoDB test failed: {e}")

    finally:
        adapter.close_connections()


if __name__ == "__main__":
    test_mongodb_connection()
