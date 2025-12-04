#!/usr/bin/env python3
"""
Explore Users Collection for Summaries
"""

import os
import sys
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
import json

# Load environment
load_dotenv()


def explore_users_collection():
    """Explore users collection to find summaries data."""

    # Get connection details
    connection_string = os.getenv("MONGODB_CONNECTION_STRING")
    database_name = os.getenv("MONGODB_DATABASE_NAME", "hackathon")

    print(f"🔍 Exploring Users Collection for Summaries...")
    print(f"Database: {database_name}")
    print()

    try:
        # Create client
        client = MongoClient(connection_string)
        db = client[database_name]
        users_collection = db["users"]

        # Get all users
        print("📊 Users Collection Analysis:")
        total_users = users_collection.count_documents({})
        print(f"Total users: {total_users}")

        # Get all users and analyze structure
        users = list(users_collection.find({}))

        print(f"\n👥 All Users:")
        for i, user in enumerate(users, 1):
            print(f"\n--- User {i} ---")
            print(f"ID: {user.get('_id')}")

            # Look for fields that might contain summaries
            summary_fields = []
            for key, value in user.items():
                if "summary" in key.lower() or "summaries" in key.lower():
                    summary_fields.append(key)
                elif isinstance(value, (list, dict)) and value:
                    # Check nested structures
                    if isinstance(value, list) and len(value) > 0:
                        if isinstance(value[0], dict):
                            print(f"  {key}: List with {len(value)} items")
                            print(f"    Sample item keys: {list(value[0].keys())}")
                    elif isinstance(value, dict):
                        print(f"  {key}: Object with keys: {list(value.keys())}")

            if summary_fields:
                print(f"📝 Summary fields found: {summary_fields}")
                for field in summary_fields:
                    print(f"  {field}: {user[field]}")

        # Search for documents containing summary-like data
        print(f"\n🔎 Searching for summary-related data...")

        # Search in different collections that might contain summaries
        collections_to_check = ["WH_Note", "flash_cards", "quiz_answer"]

        for coll_name in collections_to_check:
            print(f"\n📂 Checking {coll_name} collection:")
            collection = db[coll_name]
            count = collection.count_documents({})
            print(f"  Documents: {count}")

            if count > 0:
                sample_docs = list(collection.find({}).limit(3))
                for j, doc in enumerate(sample_docs, 1):
                    print(f"\n  --- Sample Document {j} ---")
                    print(f"  Keys: {list(doc.keys())}")

                    # Show content preview for text fields
                    for key, value in doc.items():
                        if key.startswith("_"):
                            continue
                        if isinstance(value, str) and len(value) > 50:
                            print(f"  {key}: {value[:100]}...")
                        elif isinstance(value, (list, dict)) and value:
                            if isinstance(value, list):
                                print(f"  {key}: List with {len(value)} items")
                                if len(value) > 0 and isinstance(value[0], dict):
                                    print(
                                        f"    First item keys: {list(value[0].keys())}"
                                    )
                            else:
                                print(f"  {key}: {value}")
                        else:
                            print(f"  {key}: {value}")

        print(f"\n✅ Exploration completed!")
        return users

    except Exception as e:
        print(f"\n❌ Exploration failed: {e}")
        return []

    finally:
        try:
            client.close()
        except:
            pass


if __name__ == "__main__":
    users_data = explore_users_collection()
