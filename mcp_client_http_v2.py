# mcp_client_http_v2.py - Robust version with error handling
import json
import time
import requests
from typing import TypedDict, Any, Dict
import os
import sys

print("="*80)
print("🚀 MCP AGENT CLIENT STARTING")
print("="*80)

# Test imports
print("\n📦 Loading dependencies...")
try:
    from langgraph.graph import StateGraph, END
    print("✅ LangGraph loaded")
except ImportError as e:
    print(f"❌ LangGraph import failed: {e}")
    print("Run: pip install langgraph")
    sys.exit(1)

try:
    from groq import Groq
    print("✅ Groq loaded")
except ImportError as e:
    print(f"❌ Groq import failed: {e}")
    print("Run: pip install groq")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    print("✅ dotenv loaded")
except ImportError as e:
    print(f"❌ dotenv import failed: {e}")
    print("Run: pip install python-dotenv")
    sys.exit(1)

# Load environment
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    print("\n❌ ERROR: GROQ_API_KEY not found in .env file")
    print("Add this to your .env file:")
    print("GROQ_API_KEY=your_key_here")
    sys.exit(1)

print(f"✅ GROQ_API_KEY loaded ({groq_api_key[:10]}...)")

# Initialize Groq
try:
    client = Groq(api_key=groq_api_key)
    print("✅ Groq client initialized")
except Exception as e:
    print(f"❌ Failed to initialize Groq: {e}")
    sys.exit(1)

# Check server connection
server_url = "http://localhost:5000"
print(f"\n🌐 Connecting to server at {server_url}...")

max_retries = 5
for i in range(max_retries):
    try:
        response = requests.get(f"{server_url}/health", timeout=2)
        if response.status_code == 200:
            print(f"✅ Server connected: {response.json()}")
            break
    except requests.exceptions.RequestException as e:
        if i < max_retries - 1:
            print(f"⏳ Attempt {i+1}/{max_retries}: Waiting for server...")
            time.sleep(2)
        else:
            print(f"\n❌ Server not responding after {max_retries} attempts")
            print("Make sure the server is running:")
            print("  python mcp_server_http.py")
            sys.exit(1)

# Tool calling function
def call_mcp_tool(tool: str, arguments: Dict):
    """Call MCP tool via HTTP"""
    try:
        print(f"  🔧 Calling tool: {tool} with args: {arguments}")
        response = requests.post(
            f"{server_url}/tools/call",
            json={"name": tool, "arguments": arguments},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Tool call successful")
            return result
        else:
            print(f"  ❌ Tool call failed: HTTP {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"  ❌ Tool call exception: {e}")
        return {"success": False, "error": f"Request failed: {str(e)}"}

# Agent state
class S(TypedDict):
    msg: str
    tool_result: Any
    result: str

# Route request
def route_request(state: S):
    """Use Groq LLM to determine which tool to use"""
    print(f"\n🤖 Processing: '{state['msg']}'")
    
    routing_prompt = f"""Analyze this user request and determine which tool to use:

User request: {state["msg"]}

Available tools:
1. get_weather - Get current weather for a city. Requires: city name
2. web_search - Search the web for information. Requires: search query

Respond in JSON format with:
{{
    "tool": "get_weather" | "web_search" | "none",
    "parameters": {{"city": "..."}} or {{"query": "..."}} or null,
    "reasoning": "brief explanation"
}}

Only use tools if clearly needed. For general conversation, use "none"."""

    try:
        print("  🧠 Asking Groq to route request...")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a tool routing assistant. Always respond with valid JSON."},
                {"role": "user", "content": routing_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        routing_decision = json.loads(response.choices[0].message.content)
        tool = routing_decision.get("tool")
        params = routing_decision.get("parameters")
        reasoning = routing_decision.get("reasoning")
        
        print(f"  💡 Decision: {reasoning}")
        print(f"  🎯 Selected tool: {tool}")
        
        if tool == "get_weather" and params:
            result = call_mcp_tool("get_weather", params)
            return {"msg": state["msg"], "tool_result": result}
        
        elif tool == "web_search" and params:
            result = call_mcp_tool("web_search", params)
            return {"msg": state["msg"], "tool_result": result}
        
        else:
            print("  ℹ️ No tool needed")
            return {"msg": state["msg"], "tool_result": None}
            
    except Exception as e:
        print(f"  ⚠️ Routing error: {e}")
        return {"msg": state["msg"], "tool_result": None}

# Generate response
def generate_response(state: S):
    """Use Groq to generate natural language response"""
    print("\n📝 Generating response...")
    
    try:
        tool_result = state.get("tool_result")
        
        if tool_result is None:
            # No tool used - direct response
            print("  💬 Generating direct response...")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": state["msg"]}
                ],
                temperature=0.7
            )
            return {
                "msg": state["msg"],
                "tool_result": None,
                "result": response.choices[0].message.content
            }
        
        # Check tool success
        if not tool_result.get("success"):
            error_msg = tool_result.get("error", "Unknown error")
            print(f"  ⚠️ Tool failed: {error_msg}")
            return {
                "msg": state["msg"],
                "tool_result": tool_result,
                "result": f"I encountered an error: {error_msg}"
            }
        
        # Format successful tool result
        print("  🎨 Formatting tool results...")
        tool_data = json.dumps(tool_result.get("data"), indent=2)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Use the tool results to answer naturally and concisely."},
                {"role": "user", "content": f"Question: {state['msg']}\n\nTool results:\n{tool_data}\n\nProvide a helpful answer (max 100 words)."}
            ],
            temperature=0.7
        )
        
        return {
            "msg": state["msg"],
            "tool_result": tool_result,
            "result": response.choices[0].message.content
        }
    except Exception as e:
        print(f"  ❌ Response generation error: {e}")
        return {
            "msg": state["msg"],
            "tool_result": state.get("tool_result"),
            "result": f"Error generating response: {str(e)}"
        }

# Build workflow
print("\n🏗️ Building LangGraph workflow...")
g = StateGraph(S)
g.add_node("route", route_request)
g.add_node("respond", generate_response)
g.set_entry_point("route")
g.add_edge("route", "respond")
g.add_edge("respond", END)
graph = g.compile()
print("✅ Workflow ready")

# Run tests
print("\n" + "="*80)
print("🧪 RUNNING TESTS")
print("="*80)

test_queries = [
    "What's the weather in Lagos?",
    "Search for latest developments in quantum computing",
    "Hello, how are you doing today?",
]

for i, query in enumerate(test_queries, 1):
    print("\n" + "="*80)
    print(f"TEST {i}/{len(test_queries)}")
    print("="*80)
    print(f"👤 USER: {query}")
    print("-"*80)
    
    try:
        result = graph.invoke({"msg": query})
        print("\n" + "-"*80)
        print(f"🤖 AGENT: {result['result']}")
        print("="*80)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Rate limit protection
    if i < len(test_queries):
        time.sleep(2)

print("\n" + "="*80)
print("✅ ALL TESTS COMPLETE")
print("="*80)