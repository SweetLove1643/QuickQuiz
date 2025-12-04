#!/usr/bin/env python3
"""
Test RAG API with MongoDB Data
"""

import requests
import json

API_BASE = "http://localhost:8006"


def test_chat_quick():
    """Test quick chat endpoint với MongoDB data."""
    print("🧪 Testing /chat/quick endpoint...")

    # Quick chat uses GET with query parameters
    params = {"query": "What is network layered model?", "temperature": 0.7, "top_k": 3}

    try:
        response = requests.post(f"{API_BASE}/chat/quick", params=params, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print("✅ Quick chat successful!")

            # Debug: Print all keys in response
            print(f"Response keys: {list(result.keys())}")

            # Handle different possible response field names
            response_text = (
                result.get("response")
                or result.get("answer")
                or result.get("message", "No response")
            )
            print(f"Response: {str(response_text)[:200]}...")
            print(f"Retrieved docs: {len(result.get('retrieved_documents', []))}")

            # Show retrieved documents
            for i, doc in enumerate(result.get("retrieved_documents", [])[:2], 1):
                print(
                    f"  Doc {i}: {doc.get('topic')} - Score: {doc.get('similarity_score', 0):.3f}"
                )
                print(f"         {doc.get('content', '')[:100]}...")

        else:
            print(f"❌ Quick chat failed: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error testing quick chat: {e}")


def test_chat_with_conversation():
    """Test regular chat endpoint với conversation."""
    print("\n🧪 Testing /chat endpoint...")

    url = f"{API_BASE}/chat"

    payload = {
        "query": "Tell me about Host Layers and Media Layers",
        "temperature": 0.5,
    }

    try:
        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print("✅ Chat with conversation successful!")
            print(f"Conversation ID: {result.get('conversation_id')}")

            # Debug: Print all keys in response
            print(f"Response keys: {list(result.keys())}")

            # Handle different possible response field names
            response_text = (
                result.get("response")
                or result.get("answer")
                or result.get("message", "No response")
            )
            print(f"Response: {str(response_text)[:200]}...")
            print(f"Retrieved docs: {len(result.get('retrieved_documents', []))}")

            return result.get("conversation_id")
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"❌ Error testing chat: {e}")
        return None


def test_conversation_continue(conversation_id):
    """Test continuing conversation."""
    if not conversation_id:
        return

    print(f"\n🧪 Testing conversation continuation...")

    url = f"{API_BASE}/conversations/{conversation_id}/chat"

    payload = {
        "query": "Can you explain more about Application Layer?",
        "temperature": 0.5,
    }

    try:
        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print("✅ Conversation continuation successful!")

            # Handle different possible response field names
            response_text = (
                result.get("response")
                or result.get("answer")
                or result.get("message", "No response")
            )
            print(f"Response: {str(response_text)[:200]}...")
        else:
            print(f"❌ Conversation continuation failed: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error testing conversation continuation: {e}")


def test_health():
    """Test health endpoint."""
    print("\n🧪 Testing /health endpoint...")

    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)

        if response.status_code == 200:
            result = response.json()
            print("✅ Health check successful!")
            print(f"Status: {result['status']}")
            print(
                f"MongoDB documents: {result.get('retriever', {}).get('total_documents', 'N/A')}"
            )
        else:
            print(f"❌ Health check failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Error testing health: {e}")


if __name__ == "__main__":
    print("🚀 Testing RAG API with MongoDB Data\n")

    # Test health first
    test_health()

    # Test quick chat
    test_chat_quick()

    # Test regular chat with conversation
    conversation_id = test_chat_with_conversation()

    # Continue conversation
    test_conversation_continue(conversation_id)

    print("\n🎉 All tests completed!")
