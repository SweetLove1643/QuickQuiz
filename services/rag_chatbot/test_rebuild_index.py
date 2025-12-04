#!/usr/bin/env python3
"""
Test script cho endpoint /admin/rebuild-index
Kiểm tra xem rebuild có thực sự hoạt động không.
"""

import requests
import json
import os
from datetime import datetime
import time

API_BASE_URL = "http://localhost:8006"
FAISS_DIR = "faiss_db_mongodb"


def get_file_stats(file_path):
    """Get file statistics."""
    try:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            return {
                "exists": True,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        else:
            return {"exists": False}
    except Exception as e:
        return {"error": str(e)}


def check_faiss_db_status():
    """Check current FAISS database status."""
    print("📊 Checking current FAISS database status...")

    # Check each file
    files_to_check = ["index.faiss", "index.pkl", "documents_metadata.json"]

    stats = {}
    for filename in files_to_check:
        file_path = os.path.join(FAISS_DIR, filename)
        stats[filename] = get_file_stats(file_path)

    print(json.dumps(stats, indent=2))
    return stats


def test_health_endpoint():
    """Test health endpoint trước khi rebuild."""
    print("\n🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(
                f"   Total documents: {data.get('data', {}).get('total_documents', 'N/A')}"
            )
            print(
                f"   Total vectors: {data.get('data', {}).get('total_vectors', 'N/A')}"
            )
            return data
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return None


def test_rebuild_index():
    """Test rebuild index endpoint."""
    print("\n🔄 Testing /admin/rebuild-index endpoint...")

    try:
        # Record start time
        start_time = time.time()

        # Call rebuild endpoint
        response = requests.post(f"{API_BASE_URL}/admin/rebuild-index")

        # Record end time
        end_time = time.time()
        rebuild_duration = end_time - start_time

        print(f"⏱️ Rebuild took: {rebuild_duration:.2f} seconds")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Rebuild successful!")
            print(f"   Message: {data.get('message', 'N/A')}")

            # Print detailed stats if available
            stats = data.get("stats", {})
            if stats:
                print(f"   Stats after rebuild:")
                if "vector_store" in stats:
                    vs_stats = stats["vector_store"]
                    print(
                        f"     - Total vectors: {vs_stats.get('total_vectors', 'N/A')}"
                    )
                    print(
                        f"     - Total documents: {vs_stats.get('total_documents', 'N/A')}"
                    )
                    print(
                        f"     - Index size: {vs_stats.get('index_size_mb', 'N/A')} MB"
                    )
                    print(f"     - Is loaded: {vs_stats.get('is_loaded', 'N/A')}")

                if "mongodb_loader" in stats:
                    ml_stats = stats["mongodb_loader"]
                    print(
                        f"     - MongoDB documents: {ml_stats.get('total_documents', 'N/A')}"
                    )
                    print(
                        f"     - MongoDB collections: {ml_stats.get('collections_count', 'N/A')}"
                    )

            return data
        else:
            print(f"❌ Rebuild failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Rebuild request error: {e}")
        return None


def test_stats_endpoint():
    """Test stats endpoint after rebuild."""
    print("\n📈 Testing /stats endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats retrieved successfully")

            # Print key stats
            retriever_stats = data.get("retriever_stats", {})
            if retriever_stats:
                print(f"   Retriever stats:")
                if "vector_store" in retriever_stats:
                    vs = retriever_stats["vector_store"]
                    print(f"     - Vectors: {vs.get('total_vectors', 'N/A')}")
                    print(f"     - Documents: {vs.get('total_documents', 'N/A')}")
                    print(f"     - Loaded: {vs.get('is_loaded', 'N/A')}")
                    print(f"     - Size: {vs.get('index_size_mb', 'N/A')} MB")

            return data
        else:
            print(f"❌ Stats failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return None


def test_search_after_rebuild():
    """Test document search sau khi rebuild."""
    print("\n🔍 Testing document search after rebuild...")
    try:
        params = {"query": "network layered model", "top_k": 3, "threshold": 0.3}

        response = requests.get(f"{API_BASE_URL}/search/documents", params=params)
        if response.status_code == 200:
            data = response.json()
            results_count = data.get("results_count", 0)
            print(f"✅ Search successful - Found {results_count} results")

            # Show first few results
            documents = data.get("documents", [])
            for i, doc in enumerate(documents[:2]):
                print(f"   Result {i+1}:")
                print(f"     - Topic: {doc.get('topic', 'N/A')}")
                print(f"     - Category: {doc.get('category', 'N/A')}")
                print(f"     - Score: {doc.get('similarity_score', 'N/A'):.3f}")
                print(f"     - Content preview: {doc.get('content', '')[:100]}...")

            return data
        else:
            print(f"❌ Search failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Search error: {e}")
        return None


def main():
    """Main test function."""
    print("🧪 Testing /admin/rebuild-index endpoint functionality")
    print("=" * 60)

    # Step 1: Check initial FAISS DB status
    print("\n📋 STEP 1: Check initial FAISS database status")
    initial_stats = check_faiss_db_status()

    # Step 2: Test health endpoint
    print("\n📋 STEP 2: Test health endpoint")
    health_before = test_health_endpoint()

    # Step 3: Test rebuild index
    print("\n📋 STEP 3: Test rebuild index endpoint")
    rebuild_result = test_rebuild_index()

    # Step 4: Check FAISS DB status after rebuild
    print("\n📋 STEP 4: Check FAISS database status after rebuild")
    final_stats = check_faiss_db_status()

    # Step 5: Compare before and after
    print("\n📋 STEP 5: Compare before vs after rebuild")
    for filename in ["index.faiss", "index.pkl", "documents_metadata.json"]:
        initial = initial_stats.get(filename, {})
        final = final_stats.get(filename, {})

        print(f"\n{filename}:")
        print(
            f"   Before - Size: {initial.get('size', 'N/A')} bytes, Modified: {initial.get('modified', 'N/A')}"
        )
        print(
            f"   After  - Size: {final.get('size', 'N/A')} bytes, Modified: {final.get('modified', 'N/A')}"
        )

        # Check if file was actually updated
        if initial.get("modified") != final.get("modified"):
            print(f"   ✅ File was updated during rebuild")
        else:
            print(f"   ⚠️ File timestamp unchanged - rebuild may not have worked")

    # Step 6: Test stats endpoint
    print("\n📋 STEP 6: Test stats endpoint after rebuild")
    stats_after = test_stats_endpoint()

    # Step 7: Test search functionality
    print("\n📋 STEP 7: Test search functionality")
    search_result = test_search_after_rebuild()

    # Final summary
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")

    if rebuild_result:
        print("✅ Rebuild endpoint responded successfully")
    else:
        print("❌ Rebuild endpoint failed")

    # Check if metadata file was fixed
    metadata_after = final_stats.get("documents_metadata.json", {})
    if metadata_after.get("size", 0) > 0:
        print("✅ documents_metadata.json was populated")
    else:
        print("❌ documents_metadata.json is still empty")

    if search_result and search_result.get("results_count", 0) > 0:
        print("✅ Search is working after rebuild")
    else:
        print("❌ Search not working after rebuild")

    print("\n🔚 Test completed!")


if __name__ == "__main__":
    main()
