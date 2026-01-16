# mcp_server_http.py - HTTP-based MCP Server (Windows Compatible)
from flask import Flask, request, jsonify
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------- API CONFIGURATION ----------------
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# ---------------- FLASK APP ----------------
app = Flask(__name__)

# ---------------- INPUT SCHEMAS ----------------
class WeatherInput(BaseModel):
    city: str

class WebSearchInput(BaseModel):
    query: str

# ---------------- TOOL 1: WEATHER ----------------
def get_weather(city: str):
    """Get current weather for a city using free weather API"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            current = data["current_condition"][0]
            location = data["nearest_area"][0]
            
            weather_info = {
                "location": f"{location['areaName'][0]['value']}, {location['country'][0]['value']}",
                "temperature": f"{current['temp_C']}°C / {current['temp_F']}°F",
                "condition": current["weatherDesc"][0]["value"],
                "humidity": f"{current['humidity']}%",
                "wind": f"{current['windspeedKmph']} km/h",
                "feels_like": f"{current['FeelsLikeC']}°C"
            }
            return {"success": True, "data": weather_info}
        else:
            return {"success": False, "error": f"Could not fetch weather for {city}"}
    except Exception as e:
        return {"success": False, "error": f"Weather API error: {str(e)}"}

# ---------------- TOOL 2: WEB SEARCH ----------------
def web_search(query: str):
    """Search the web using Serper API"""
    if not SERPER_API_KEY:
        return {"success": False, "error": "SERPER_API_KEY not configured"}
    
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {"q": query, "num": 5}
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            for item in data.get("organic", [])[:5]:
                results.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet")
                })
            
            knowledge = data.get("knowledgeGraph", {})
            
            return {
                "success": True,
                "data": {
                    "query": query,
                    "results": results,
                    "knowledge_graph": knowledge.get("description", "") if knowledge else None
                }
            }
        else:
            return {"success": False, "error": f"Serper API error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Web search error: {str(e)}"}

# ---------------- HTTP ENDPOINTS ----------------
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "server": "MCP HTTP Server"})

@app.route('/tools', methods=['GET'])
def list_tools():
    """List available tools"""
    return jsonify({
        "tools": [
            {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {"city": "string"}
            },
            {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {"query": "string"}
            }
        ]
    })

@app.route('/tools/call', methods=['POST'])
def call_tool():
    """Execute a tool"""
    data = request.json
    tool_name = data.get("name")
    arguments = data.get("arguments", {})
    
    if tool_name == "get_weather":
        city = arguments.get("city")
        if not city:
            return jsonify({"success": False, "error": "Missing 'city' parameter"}), 400
        result = get_weather(city)
        return jsonify(result)
    
    elif tool_name == "web_search":
        query = arguments.get("query")
        if not query:
            return jsonify({"success": False, "error": "Missing 'query' parameter"}), 400
        result = web_search(query)
        return jsonify(result)
    
    else:
        return jsonify({"success": False, "error": f"Unknown tool: {tool_name}"}), 404

# ---------------- SERVER ENTRY POINT ----------------
if __name__ == "__main__":
    print("🔥 MCP HTTP Server starting...")
    print("📡 Server will run on http://localhost:5000")
    print("✅ Ready to accept requests!")
    app.run(host="0.0.0.0", port=5000, debug=False)