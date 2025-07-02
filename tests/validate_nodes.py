#!/usr/bin/env python3
"""
Test script to verify the Shrug Prompter ComfyUI nodes work with edge-llm server.
Run this from the shrug-prompter directory.
"""

import sys
import asyncio
import requests
from utils import get_models
from shrug_router import send_request

def test_server_connection(base_url="http://localhost:8080"):
    """Test if the edge-llm server is running."""
    print("=" * 50)
    print("Testing server connection...")

    try:
        response = requests.get(f"{base_url}/v1/models", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
            print(f"✓ Server is running at {base_url}")
            print(f"  Available models: {models}")
            return True, models
        else:
            print(f"✗ Server returned HTTP {response.status_code}")
            return False, []
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        print(f"  Make sure edge-llm is running on {base_url}")
        return False, []

def test_model_fetching():
    """Test the get_models utility function."""
    print("=" * 50)
    print("Testing model fetching...")

    try:
        models = get_models(
            provider="openai",
            api_key="not-required",
            base_url="http://localhost:8080"
        )
        print(f"✓ Model fetching works")
        print(f"  Found models: {models}")
        return models
    except Exception as e:
        print(f"✗ Model fetching failed: {e}")
        return []

async def test_text_request(model_name):
    """Test a simple text request."""
    print("=" * 50)
    print("Testing text request...")

    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello and count to 3."}
        ]

        response = await send_request(
            provider="openai",
            base_url="http://localhost:8080",
            api_key="not-required",
            llm_model=model_name,
            messages=messages,
            max_tokens=50,
            temperature=0.1,
            top_p=0.95
        )

        if "error" in response:
            print(f"✗ Request failed: {response['error']}")
            return False
        else:
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✓ Text request successful")
            print(f"  Response: {content[:100]}...")
            return True
    except Exception as e:
        print(f"✗ Text request failed: {e}")
        return False

async def test_vision_request(model_name):
    """Test a vision request with a simple image."""
    print("=" * 50)
    print("Testing vision request...")

    # Skip if model doesn't support vision
    if "(Vision)" not in model_name and "vlm" not in model_name.lower() and "vision" not in model_name.lower():
        print("⚠ Skipping vision test - model doesn't appear to support vision")
        return True

    try:
        # Simple test image URL (small image)
        test_image_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        messages = [
            {"role": "system", "content": "You are a vision assistant. Describe images briefly."},
            {"role": "user", "content": [
                {"type": "text", "text": "What do you see in this image?"},
                {"type": "image_url", "image_url": {"url": test_image_url}}
            ]}
        ]

        response = await send_request(
            provider="openai",
            base_url="http://localhost:8080",
            api_key="not-required",
            llm_model=model_name.replace(" (Vision)", ""),
            messages=messages,
            max_tokens=100,
            temperature=0.1,
            top_p=0.95
        )

        if "error" in response:
            print(f"✗ Vision request failed: {response['error']}")
            return False
        else:
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✓ Vision request successful")
            print(f"  Response: {content[:100]}...")
            return True
    except Exception as e:
        print(f"✗ Vision request failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("Shrug Prompter + Edge-LLM Test Suite")
    print("=" * 50)

    # Test 1: Server connection
    connected, available_models = test_server_connection()
    if not connected:
        print("\n❌ Server connection failed. Please start edge-llm server first.")
        return False

    # Test 2: Model fetching
    fetched_models = test_model_fetching()
    if not fetched_models or "Error" in str(fetched_models):
        print("\n❌ Model fetching failed.")
        return False

    # Pick a model for testing
    test_model = available_models[0] if available_models else "unknown"

    # Test 3: Text request
    text_success = await test_text_request(test_model)
    if not text_success:
        print("\n❌ Text request failed.")
        return False

    # Test 4: Vision request (if supported)
    vision_success = await test_vision_request(test_model)
    if not vision_success:
        print("\n⚠ Vision request failed (might not be supported by this model).")

    print("=" * 50)
    if text_success:
        print("✅ All core tests passed! Shrug Prompter should work with your edge-llm server.")
        print("\nNext steps:")
        print("1. Make sure ComfyUI is running")
        print("2. Load a workflow with Shrug Prompter nodes")
        print("3. Set base_url to 'http://localhost:8080' in Provider Selector")
        print("4. Set api_key to anything (not required for local server)")
        return True
    else:
        print("❌ Some tests failed. Check edge-llm server logs for errors.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
