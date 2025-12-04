#!/usr/bin/env python3
"""
Test script để debug sự khác biệt giữa /chat/quick và /chat endpoints
"""

import requests
import json

base_url = "http://localhost:8006"
test_query = "Python là gì"

print("=== TESTING API ENDPOINTS ===\n")

# Test 1: /chat/quick (working)
print("1. Testing /chat/quick (should work):")
try:
    response = requests.post(
        f"{base_url}/chat/quick",
        params={"query": test_query, "top_k": 5, "temperature": 0.7},
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Sources count: {data.get('sources_count', 0)}")
        print(f"Conversation ID: {data.get('conversation_id')}")
        print(f"Answer preview: {data.get('answer', '')[:100]}...")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")

print("\n" + "=" * 50 + "\n")

# Test 2: /chat (problematic)
print("2. Testing /chat (has issues):")
try:
    response = requests.post(
        f"{base_url}/chat",
        json={
            "query": test_query,
            "retrieval_config": {"top_k": 5, "similarity_threshold": 0.3},
            "chat_config": {"temperature": 0.7, "max_tokens": 500},
        },
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Sources count: {data.get('context', {}).get('retrieved_count', 0)}")
        print(f"Conversation ID: {data.get('conversation_id')}")
        print(f"Answer preview: {data.get('answer', '')[:100]}...")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")

print("\n" + "=" * 50 + "\n")

# Test 3: Health check
print("3. Testing health check:")
try:
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Documents: {data.get('data', {}).get('total_documents', 0)}")
        print(f"Vectors: {data.get('data', {}).get('total_vectors', 0)}")
except Exception as e:
    print(f"Request failed: {e}")

print("\n=== TEST COMPLETE ===")
