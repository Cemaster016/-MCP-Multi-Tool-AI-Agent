# mcp_client_http.py - HTTP-based MCP Client (Windows Compatible)
import subprocess
import json
import sys
import time
import requests
from langgraph.graph import StateGraph, END
from typing import TypedDict, Any, Dict
from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# ---------------- GROQ CLIENT ----------------
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------- START MCP SERVER ----------------
print("🚀 Starting MCP HTTP server...")

# Start server in background
server = subprocess.Popen(
    [sys.executable, "mcp_server_http.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for server to be ready
print("⏳ Waiting for server to start...")
time.sleep(3)

# Check if server is running
max_retries = 10
server_url = "http://localhost:5000"

for i in range(max_retries):
    try:
        response = requests.get(f"{server_url}/health", timeout=2)
        if response.status_code == 200:
            print("✅ MCP HTTP server is ready!")
            break
    except requests.exceptions.RequestException:
        if i < max_retries - 1:
            print(f"⏳ Retry {i+1}/{max_retries}...")
            time.sleep(1)
        else:
            print("❌ Server failed to start!")
            server.terminate()
            sys.exit(1)

# ---------------- TOOL CALLING ----------------
def call_mcp_tool(tool: str, arguments: Dict):
    """Call MCP tool via HTTP"""
    try:
        response = requests.post(
            f"{server_url}/tools/call",
            json={"name": tool, "arguments": arguments},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}

# ---------------- AGENT STATE ----------------
class S(TypedDict):
    msg: str
    tool_result: Any
    result: str

# ---------------- AGENT LOGIC ----------------
def route_request(state: S):
    """Use Groq LLM to determine which tool to use"""
    
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
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a tool routing assistant. Analyze user requests and determine which tool to use. Always respond with valid JSON."},
                {"role": "user", "content": routing_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        routing_decision = json.loads(response.choices[0].message.content)
        tool = routing_decision.get("tool")
        params = routing_decision.get("parameters")
        
        print(f"🤖 Routing: {routing_decision.get('reasoning')}")
        
        if tool == "get_weather" and params:
            result = call_mcp_tool("get_weather", params)
            return {"msg": state["msg"], "tool_result": result}
        
        elif tool == "web_search" and params:
            result = call_mcp_tool("web_search", params)
            return {"msg": state["msg"], "tool_result": result}
        
        else:
            return {"msg": state["msg"], "tool_result": None}
            
    except Exception as e:
        print(f"⚠️ Routing error: {e}")
        return {"msg": state["msg"], "tool_result": None}

def generate_response(state: S):
    """Use Groq to generate natural language response"""
    try:
        tool_result = state.get("tool_result")
        
        if tool_result is None:
            # No tool used
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
        
        # Check if tool call was successful
        if not tool_result.get("success"):
            error_msg = tool_result.get("error", "Unknown error")
            return {
                "msg": state["msg"],
                "tool_result": tool_result,
                "result": f"I encountered an error: {error_msg}"
            }
        
        # Format successful tool result
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
        return {
            "msg": state["msg"],
            "tool_result": state.get("tool_result"),
            "result": f"Error: {str(e)}"
        }

# ---------------- LANGGRAPH WORKFLOW ----------------
g = StateGraph(S)
g.add_node("route", route_request)
g.add_node("respond", generate_response)
g.set_entry_point("route")
g.add_edge("route", "respond")
g.add_edge("respond", END)
graph = g.compile()

# ---------------- TESTING ----------------
print("\n" + "="*80)
print("🧪 TESTING MCP AGENT")
print("="*80 + "\n")

tests = [
    "What's the weather in Lagos?",
    "Search for latest AI breakthroughs in 2025",
    "Hello! How are you?",
]

for t in tests:
    print(f"\n{'='*80}")
    print(f"USER: {t}")
    print('='*80)
    try:
        result = graph.invoke({"msg": t})
        print(f"\n✨ AGENT: {result['result']}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    time.sleep(1)  # Rate limit protection

print("\n✅ Testing complete!")

# Cleanup
print("🛑 Shutting down server...")
server.terminate()
try:
    server.wait(timeout=5)
except:
    server.kill()
print("👋 Goodbye!")