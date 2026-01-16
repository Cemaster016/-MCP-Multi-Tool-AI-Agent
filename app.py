# app.py - Interactive Frontend for MCP Agent
from flask import Flask, render_template, request, jsonify, Response
import json
import time
import requests
from typing import Dict, Any
import os
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END
from typing import TypedDict
import threading
import queue

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# MCP Server URL
MCP_SERVER_URL = "http://localhost:5000"

# Message queue for streaming responses
message_queues = {}

# ============================================================================
# MCP TOOL CALLING
# ============================================================================

def call_mcp_tool(tool: str, arguments: Dict):
    """Call MCP tool via HTTP"""
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/tools/call",
            json={"name": tool, "arguments": arguments},
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}

# ============================================================================
# AGENT LOGIC
# ============================================================================

class AgentState(TypedDict):
    msg: str
    tool_result: Any
    result: str
    session_id: str

def route_request(state: AgentState):
    """Use Groq LLM to determine which tool to use"""
    session_id = state.get("session_id", "default")
    
    # Send status update
    if session_id in message_queues:
        message_queues[session_id].put({
            "type": "status",
            "message": "🤔 Analyzing your request..."
        })
    
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
        response = groq_client.chat.completions.create(
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
        
        # Send routing decision
        if session_id in message_queues:
            message_queues[session_id].put({
                "type": "routing",
                "tool": tool,
                "reasoning": reasoning
            })
        
        if tool == "get_weather" and params:
            if session_id in message_queues:
                message_queues[session_id].put({
                    "type": "status",
                    "message": f"🌤️ Getting weather for {params.get('city')}..."
                })
            result = call_mcp_tool("get_weather", params)
            return {"msg": state["msg"], "tool_result": result, "session_id": session_id}
        
        elif tool == "web_search" and params:
            if session_id in message_queues:
                message_queues[session_id].put({
                    "type": "status",
                    "message": f"🔍 Searching for: {params.get('query')}..."
                })
            result = call_mcp_tool("web_search", params)
            return {"msg": state["msg"], "tool_result": result, "session_id": session_id}
        
        else:
            return {"msg": state["msg"], "tool_result": None, "session_id": session_id}
            
    except Exception as e:
        return {"msg": state["msg"], "tool_result": None, "session_id": session_id}

def generate_response(state: AgentState):
    """Use Groq to generate natural language response"""
    session_id = state.get("session_id", "default")
    
    # Send status update
    if session_id in message_queues:
        message_queues[session_id].put({
            "type": "status",
            "message": "✍️ Crafting response..."
        })
    
    try:
        tool_result = state.get("tool_result")
        
        if tool_result is None:
            response = groq_client.chat.completions.create(
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
                "result": response.choices[0].message.content,
                "session_id": session_id
            }
        
        if not tool_result.get("success"):
            error_msg = tool_result.get("error", "Unknown error")
            return {
                "msg": state["msg"],
                "tool_result": tool_result,
                "result": f"I encountered an error: {error_msg}",
                "session_id": session_id
            }
        
        tool_data = json.dumps(tool_result.get("data"), indent=2)
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Use the tool results to answer naturally and concisely."},
                {"role": "user", "content": f"Question: {state['msg']}\n\nTool results:\n{tool_data}\n\nProvide a helpful answer (max 150 words)."}
            ],
            temperature=0.7
        )
        
        return {
            "msg": state["msg"],
            "tool_result": tool_result,
            "result": response.choices[0].message.content,
            "session_id": session_id
        }
    except Exception as e:
        return {
            "msg": state["msg"],
            "tool_result": state.get("tool_result"),
            "result": f"Error generating response: {str(e)}",
            "session_id": session_id
        }

# Build LangGraph workflow
graph_builder = StateGraph(AgentState)
graph_builder.add_node("route", route_request)
graph_builder.add_node("respond", generate_response)
graph_builder.set_entry_point("route")
graph_builder.add_edge("route", "respond")
graph_builder.add_edge("respond", END)
agent_graph = graph_builder.compile()

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Render main chat interface"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    # Check if MCP server is running
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health", timeout=2)
        mcp_status = "online" if response.status_code == 200 else "offline"
    except:
        mcp_status = "offline"
    
    return jsonify({
        "status": "healthy",
        "frontend": "online",
        "mcp_server": mcp_status,
        "groq_api": "configured" if os.getenv("GROQ_API_KEY") else "missing"
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Process chat message and return response"""
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        # Create message queue for this session
        message_queues[session_id] = queue.Queue()
        
        # Process message in background
        def process_message():
            result = agent_graph.invoke({
                "msg": user_message,
                "session_id": session_id
            })
            message_queues[session_id].put({
                "type": "final",
                "response": result['result']
            })
        
        thread = threading.Thread(target=process_message)
        thread.start()
        
        return jsonify({"status": "processing", "session_id": session_id})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stream/<session_id>')
def stream(session_id):
    """Server-Sent Events endpoint for real-time updates"""
    def generate():
        if session_id not in message_queues:
            message_queues[session_id] = queue.Queue()
        
        q = message_queues[session_id]
        
        while True:
            try:
                message = q.get(timeout=30)
                yield f"data: {json.dumps(message)}\n\n"
                
                if message.get("type") == "final":
                    # Clean up queue after final message
                    if session_id in message_queues:
                        del message_queues[session_id]
                    break
            except queue.Empty:
                # Send keepalive
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("="*80)
    print("🚀 MCP AGENT FRONTEND STARTING")
    print("="*80)
    print(f"📡 Frontend URL: http://localhost:8000")
    print(f"🔧 MCP Server: {MCP_SERVER_URL}")
    print("="*80)
    
    # Check MCP server
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ MCP Server is running")
        else:
            print("⚠️  MCP Server returned unexpected status")
    except:
        print("❌ MCP Server is not running!")
        print("   Start it with: python mcp_server_http.py")
    
    print("\n🌐 Open http://localhost:8000 in your browser")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)