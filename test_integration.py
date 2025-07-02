#!/usr/bin/env python3
"""
Simple validation script for Shrug Prompter + Edge LLM integration.
Run this from the shrug-prompter directory.

Usage: python test_integration.py
"""

import requests
import asyncio
import aiohttp
import json

#!/usr/bin/env python3
"""
Simple validation script for Shrug Prompter + Edge LLM integration.
Run this from the shrug-prompter directory.

Usage:
    python test_integration.py                           # Test localhost:8080
    python test_integration.py --server 192.168.1.100   # Test remote server
    python test_integration.py --server localhost:8080  # Test specific port
"""

import requests
import asyncio
import aiohttp
import json
import argparse
import sys

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test Shrug Prompter + Edge LLM integration")
    parser.add_argument(
        "--server",
        default="localhost:8080",
        help="Server address and port (default: localhost:8080)"
    )
    return parser.parse_args()

def test_edge_llm_server(server_address):
    """Test if edge-llm server is running and responsive."""
    # Ensure proper URL format
    if not server_address.startswith(('http://', 'https://')):
        base_url = f"http://{server_address}"
    else:
        base_url = server_address.rstrip('/')

    print(f"🔍 Testing edge-llm server connection at {base_url}...")

    try:
        # Test /v1/models endpoint
        response = requests.get(f"{base_url}/v1/models", timeout=15)
        if response.status_code == 200:
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
            print(f"✅ Server is running at {base_url}")
            print(f"   Available models: {models}")
            return True, models, base_url
        else:
            print(f"❌ Server returned HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False, [], base_url
    except requests.ConnectionError:
        print(f"❌ Cannot connect to {base_url}")
        print("   Possible solutions:")
        print("   1. Make sure edge-llm server is running")
        print("   2. Check the server address and port")
        print("   3. Ensure firewall allows the connection")
        print("   4. If on different machines, use the server's IP address")
        return False, [], base_url
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, [], base_url

async def test_chat_request(base_url, model_name):
    """Test a simple chat request to the server."""
    print(f"🤖 Testing chat request with model: {model_name}")

    endpoint = f"{base_url}/v1/chat/completions"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello and count to 3."}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"✅ Chat request successful")
                    print(f"   Response: {content[:100]}...")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Chat request failed: HTTP {response.status}")
                    print(f"   Response: {text[:200]}")
                    return False
    except Exception as e:
        print(f"❌ Chat request error: {e}")
        return False

async def test_vision_request(base_url, model_name):
    """Test a vision request if the model supports it."""

    # Skip non-vision models
    if not any(keyword in model_name.lower() for keyword in ["vlm", "vision", "gemma3n"]):
        print(f"⏭️  Skipping vision test for {model_name} (not a vision model)")
        return True

    print(f"👁️  Testing vision request with model: {model_name}")

    # Simple 1x1 red pixel as test image
    test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/x8AAoAB/1b/nFUAAAAASUVORK5CYII="

    endpoint = f"{base_url}/v1/chat/completions"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a vision assistant. Describe images briefly."},
            {"role": "user", "content": [
                {"type": "text", "text": "What color is this image?"},
                {"type": "image_url", "image_url": {"url": test_image}}
            ]}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, timeout=90) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"✅ Vision request successful")
                    print(f"   Response: {content[:100]}...")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Vision request failed: HTTP {response.status}")
                    print(f"   Response: {text[:200]}")
                    return False
    except Exception as e:
        print(f"❌ Vision request error: {e}")
        return False

def test_comfyui_imports():
    """Test if the ComfyUI node imports work."""
    print("📦 Testing ComfyUI node imports...")

    try:
        # Test individual node imports
        from nodes.provider_selector import ShrugProviderSelector
        from nodes.response_parser import ShrugResponseParser
        print("✅ Node imports successful")

        # Test the main init
        import __init__ as shrug_init
        mappings = shrug_init.NODE_CLASS_MAPPINGS
        print(f"✅ Found {len(mappings)} node mappings")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're in the shrug-prompter directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def main():
    """Run all validation tests."""
    args = parse_args()

    print("=" * 60)
    print("🧪 Shrug Prompter + Edge LLM Integration Test")
    print("=" * 60)

    success_count = 0
    total_tests = 4

    # Test 1: ComfyUI imports
    if test_comfyui_imports():
        success_count += 1

    print()

    # Test 2: Server connection
    server_running, models, base_url = test_edge_llm_server(args.server)
    if server_running:
        success_count += 1

    if not server_running:
        print(f"\n💡 To start edge-llm server (if on same machine):")
        print("   edge-llm --host 0.0.0.0 --log-level INFO")
        print(f"\n💡 If testing across machines:")
        print(f"   1. Find your server's IP address: hostname -I")
        print(f"   2. Run: python test_integration.py --server YOUR_SERVER_IP:8080")
        print("\n🛑 Skipping remaining tests (server not available)")
        print(f"\n📊 Results: {success_count}/{total_tests} tests passed")
        return success_count == total_tests

    # Pick first available model for testing
    test_model = models[0] if models else None
    if not test_model:
        print("❌ No models available for testing")
        print(f"\n📊 Results: {success_count}/{total_tests} tests passed")
        return False

    print()

    # Test 3: Chat request
    if await test_chat_request(base_url, test_model):
        success_count += 1

    print()

    # Test 4: Vision request (if applicable)
    if await test_vision_request(base_url, test_model):
        success_count += 1

    print()
    print("=" * 60)
    print(f"📊 Results: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("🎉 All tests passed! Your setup is ready.")
        print(f"\n✨ ComfyUI Configuration:")
        print(f"   - Provider: openai")
        print(f"   - Base URL: {base_url}")
        print(f"   - API Key: not-required")
        print(f"   - Model: {test_model}")
        return True
    else:
        print(f"⚠️  {total_tests - success_count} test(s) failed. Check the errors above.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        exit(1)
