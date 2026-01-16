# test_client.py - Simple test to verify setup
import sys
print("🔍 Starting test client...")
print(f"Python version: {sys.version}")

# Test 1: Check imports
print("\n📦 Testing imports...")
try:
    import requests
    print("✅ requests")
except ImportError as e:
    print(f"❌ requests: {e}")

try:
    from groq import Groq
    print("✅ groq")
except ImportError as e:
    print(f"❌ groq: {e}")

try:
    from langgraph.graph import StateGraph, END
    print("✅ langgraph")
except ImportError as e:
    print(f"❌ langgraph: {e}")

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv")
except ImportError as e:
    print(f"❌ python-dotenv: {e}")

# Test 2: Check environment variables
print("\n🔐 Testing environment variables...")
import os
from dotenv import load_dotenv
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
serper_key = os.getenv("SERPER_API_KEY")

if groq_key:
    print(f"✅ GROQ_API_KEY found ({groq_key[:10]}...)")
else:
    print("❌ GROQ_API_KEY not found")

if serper_key:
    print(f"✅ SERPER_API_KEY found ({serper_key[:10]}...)")
else:
    print("❌ SERPER_API_KEY not found")

# Test 3: Check if server is running
print("\n🌐 Testing server connection...")
import requests
import time

server_url = "http://localhost:5000"

for i in range(3):
    try:
        response = requests.get(f"{server_url}/health", timeout=2)
        if response.status_code == 200:
            print(f"✅ Server is running: {response.json()}")
            break
    except requests.exceptions.RequestException as e:
        print(f"⏳ Attempt {i+1}/3: Server not ready - {e}")
        time.sleep(1)
else:
    print("❌ Server is not running. Start it with: python mcp_server_http.py")
    sys.exit(1)

# Test 4: Test tool call
print("\n🛠️ Testing tool call...")
try:
    response = requests.post(
        f"{server_url}/tools/call",
        json={"name": "get_weather", "arguments": {"city": "London"}},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"❌ Tool call failed: {e}")

# Test 5: Test Groq API
print("\n🤖 Testing Groq API...")
try:
    from groq import Groq
    client = Groq(api_key=groq_key)
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say hello in 5 words"}],
        temperature=0.7
    )
    print(f"✅ Groq response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Groq API failed: {e}")

print("\n✅ All tests complete!")