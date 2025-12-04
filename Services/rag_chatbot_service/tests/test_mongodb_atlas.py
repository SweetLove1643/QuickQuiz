#!/usr/bin/env python3
"""
Test MongoDB Atlas Connection

Script để test connection tới MongoDB Atlas với credentials từ .env file.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
print("📂 Loading .env file...")
env_loaded = load_dotenv()
print(f"Environment loaded: {env_loaded}")

from mongodb_adapter import MongoDBAdapter


def test_mongodb_atlas_connection():
    """Test connection tới MongoDB Atlas."""
    print("🧪 Testing MongoDB Atlas Connection...")
    print(f"📍 Database: {os.getenv('MONGODB_DATABASE_NAME', 'hackathon')}")
    print(f"📂 Collection: {os.getenv('MONGODB_COLLECTION_NAME', 'quiz_data')}")

    adapter = MongoDBAdapter()

    try:
        # Test connection
        print("🔗 Connecting to MongoDB Atlas...")
        adapter.connect_sync()

        # Get collection stats
        print("📊 Getting collection statistics...")
        stats = adapter.get_collection_stats()

        print("\n✅ Connection Successful!")
        print("=" * 50)
        print(f"Database: {stats.get('database_name')}")
        print(f"Collection: {stats.get('collection_name')}")
        print(f"Total Documents: {stats.get('total_documents', 0)}")
        print(f"Unique Topics: {stats.get('unique_topics', 0)}")
        print(f"Unique Categories: {stats.get('unique_categories', 0)}")

        # Show available topics and categories
        topics = stats.get("topics", [])
        categories = stats.get("categories", [])

        if topics:
            print(f"\n📋 Available Topics: {topics}")

        if categories:
            print(f"📂 Available Categories: {categories}")

        # Sample some documents
        print(f"\n📄 Sample Documents:")
        sample_docs = adapter.get_all_documents(limit=3)

        for i, doc in enumerate(sample_docs, 1):
            print(f"\n  Document {i}:")
            print(f"    ID: {doc.get('_id', 'N/A')}")
            print(f"    Topic: {doc.get('topic', 'N/A')}")
            print(f"    Category: {doc.get('category', 'N/A')}")

            content = doc.get("content", "")
            if isinstance(content, dict):
                # Handle nested content
                content_preview = str(content)[:100] + "..."
            else:
                content_preview = (
                    content[:100] + "..." if len(str(content)) > 100 else content
                )

            print(f"    Content: {content_preview}")

        print(f"\n🎉 MongoDB Atlas integration ready!")
        return True

    except Exception as e:
        print(f"\n❌ MongoDB Atlas connection failed:")
        print(f"Error: {e}")
        print(f"\n💡 Troubleshooting tips:")
        print("1. Check your MongoDB Atlas cluster is running")
        print("2. Verify network access (IP whitelist)")
        print("3. Confirm username/password are correct")
        print("4. Check .env file configuration")
        return False

    finally:
        try:
            adapter.close_connections()
        except:
            pass


if __name__ == "__main__":
    # Load environment variables first
    load_dotenv()

    # Show environment info
    print("🔧 Environment Configuration:")
    print(f"Username: {os.getenv('MONGO_DB_USERNAME', 'NOT_SET')}")
    print(f"Password: {'***' if os.getenv('MONGO_DB_PASSWORD') else 'NOT_SET'}")
    print(f"Database: {os.getenv('MONGODB_DATABASE_NAME', 'hackathon')}")
    print(f"Collection: {os.getenv('MONGODB_COLLECTION_NAME', 'quiz_data')}")
    print()

    # Test connection
    success = test_mongodb_atlas_connection()

    if success:
        print("\n✅ Ready to build vector database from MongoDB!")
    else:
        print("\n❌ Please fix MongoDB connection before proceeding.")

    sys.exit(0 if success else 1)
