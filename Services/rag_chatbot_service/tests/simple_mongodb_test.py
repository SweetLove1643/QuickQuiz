#!/usr/bin/env python3
"""
Simple MongoDB Connection Test
"""

import os
import sys
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient

# Load environment
load_dotenv()


def simple_mongodb_test():
    """Simple test without our custom adapter."""

    # Get connection string directly from env
    connection_string = os.getenv("MONGODB_CONNECTION_STRING")
    database_name = os.getenv("MONGODB_DATABASE_NAME", "hackathon")
    collection_name = os.getenv("MONGODB_COLLECTION_NAME", "quiz_data")

    print(f"🔧 Connection Details:")
    print(f"Database: {database_name}")
    print(f"Collection: {collection_name}")
    print(f"Connection: {connection_string[:50]}...")
    print()

    try:
        # Create client
        print("1. Creating MongoDB client...")
        client = MongoClient(connection_string)

        # Test ping
        print("2. Testing connection with ping...")
        result = client.admin.command("ping")
        print(f"   Ping result: {result}")

        # Get database
        print("3. Accessing database...")
        db = client[database_name]

        # Get collection
        print("4. Accessing collection...")
        collection = db[collection_name]

        # Count documents
        print("5. Counting documents...")
        count = collection.count_documents({})
        print(f"   Total documents: {count}")

        # Get a sample document
        if count > 0:
            print("6. Getting sample document...")
            sample_doc = collection.find_one()
            print(
                f"   Sample document keys: {list(sample_doc.keys()) if sample_doc else 'None'}"
            )
        else:
            print("6. No documents found in collection")

        # List all collections
        print("7. Listing all collections in database...")
        collections = db.list_collection_names()
        print(f"   Available collections: {collections}")

        # Check other collections for data
        print("\n8. Checking document counts in other collections...")
        for coll_name in collections:
            try:
                coll = db[coll_name]
                doc_count = coll.count_documents({})
                print(f"   {coll_name}: {doc_count} documents")

                # If collection has documents, show sample
                if doc_count > 0:
                    sample = coll.find_one()
                    if sample:
                        print(f"      Sample keys: {list(sample.keys())}")
            except Exception as e:
                print(f"   {coll_name}: Error - {e}")

        print("\n✅ MongoDB connection test successful!")
        return True

    except Exception as e:
        print(f"\n❌ MongoDB connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

    finally:
        try:
            client.close()
            print("🔒 Connection closed")
        except:
            pass


if __name__ == "__main__":
    success = simple_mongodb_test()
    sys.exit(0 if success else 1)
