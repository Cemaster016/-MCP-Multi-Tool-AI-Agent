# 🤖 MCP Multi-Tool AI Agent

An intelligent, extensible AI agent built on the **Model Context Protocol (MCP)** that orchestrates multiple tools through natural language understanding. Powered by Groq's Llama 3.3 70B and featuring a production-ready web interface.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Status](https://img.shields.io/badge/status-production-green.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

The MCP Multi-Tool AI Agent is an enterprise-grade conversational AI system that demonstrates advanced AI orchestration patterns. It intelligently routes user requests to appropriate tools (weather APIs, web search) using LLM-powered decision-making, returning natural language responses through a real-time streaming interface.

### Key Capabilities

- **Intelligent Tool Routing**: LLM analyzes requests and autonomously selects the appropriate tool
- **Real-Time Streaming**: Server-Sent Events (SSE) provide live status updates during processing
- **Extensible Architecture**: Modular MCP design allows seamless integration of new tools
- **Production-Ready**: Built with Flask, LangGraph, and proper error handling for enterprise deployment

---

## ✨ Features

### Core Functionality

- **🧠 Natural Language Understanding**: Powered by Groq's Llama 3.3 70B for intent recognition and tool selection
- **🌤️ Weather Intelligence**: Real-time weather data retrieval for any global location
- **🔍 Web Search**: Integrated Serper API for current information gathering
- **💬 Conversational AI**: Handles casual conversation when no tools are needed
- **📊 Real-Time Updates**: Live status streaming shows the agent's decision-making process

### Technical Features

- **🔄 Stateful Workflow**: LangGraph manages multi-step agent logic with proper state management
- **🔌 HTTP/REST Communication**: Reliable client-server architecture using Flask
- **🎨 Modern UI**: Responsive chat interface with gradient design and real-time indicators
- **🛡️ Error Handling**: Comprehensive exception management and retry logic
- **📈 Scalable Design**: Microservices architecture supporting horizontal scaling

---

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│              (Flask + SSE + Real-time UI)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  LangGraph Orchestrator                     │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │   Route      │───────▶│   Respond    │                  │
│  │  (Groq LLM)  │        │  (Groq LLM)  │                  │
│  └──────────────┘        └──────────────┘                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Tool Server                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Weather   │  │ Web Search  │  │   Future    │        │
│  │    Tool     │  │    Tool     │  │   Tools     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

1. **User Input** → Frontend captures message and creates session
2. **Intent Analysis** → Groq LLM analyzes query and selects tool
3. **Tool Execution** → MCP server executes selected tool
4. **Response Generation** → Groq LLM formats results naturally
5. **Streaming Response** → SSE delivers real-time updates to UI

---

## 🛠️ Technology Stack

### Backend
- **Python 3.8+**: Core runtime environment
- **Flask**: Web framework for frontend and API
- **LangGraph**: State machine for agent workflow orchestration
- **FastMCP**: Model Context Protocol implementation
- **Groq SDK**: LLM API integration (Llama 3.3 70B)
- **Requests**: HTTP client for external APIs

### Frontend
- **HTML5/CSS3**: Modern responsive UI
- **Vanilla JavaScript**: No framework overhead, pure performance
- **Server-Sent Events (SSE)**: Real-time bi-directional communication
- **CSS Grid/Flexbox**: Responsive layout system

### External APIs
- **Groq API**: Free tier LLM inference (Llama 3.3 70B)
- **Serper API**: Web search (2,500 free searches/month)
- **wttr.in**: Weather data (free, no API key required)

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Active internet connection
- Free API keys from Groq and Serper

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/mcp-agent.git
cd mcp-agent
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
fastmcp
pydantic
requests
python-dotenv
langgraph
groq
flask
```

### Step 4: Obtain API Keys

#### Groq API (Free)
1. Visit: https://console.groq.com
2. Sign up and navigate to "API Keys"
3. Click "Create API Key"
4. Copy the key

#### Serper API (Free Tier)
1. Visit: https://serper.dev
2. Sign up (2,500 free searches/month)
3. Copy API key from dashboard

### Step 5: Configure Environment

Create `.env` file in project root:

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Serper API Configuration
SERPER_API_KEY=your_serper_api_key_here
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GROQ_API_KEY` | Yes | Groq API authentication key | - |
| `SERPER_API_KEY` | Yes | Serper web search API key | - |
| `MCP_SERVER_PORT` | No | MCP server port | 5000 |
| `FRONTEND_PORT` | No | Frontend application port | 8000 |

### Server Configuration

**MCP Server (mcp_server_http.py):**
```python
app.run(host="0.0.0.0", port=5000, debug=False)
```

**Frontend Server (app.py):**
```python
app.run(host="0.0.0.0", port=8000, debug=True, threaded=True)
```

---

## 🚀 Usage

### Starting the System

#### Terminal 1: MCP Tool Server

```bash
python mcp_server_http.py
```

**Expected Output:**
```
🔥 MCP HTTP Server starting on http://localhost:5000
 * Running on http://127.0.0.1:5000
```

#### Terminal 2: Frontend Application

```bash
python app.py
```

**Expected Output:**
```
🚀 MCP AGENT FRONTEND STARTING
📡 Frontend URL: http://localhost:8000
✅ MCP Server is running
🌐 Open http://localhost:8000 in your browser
```

### Accessing the Interface

Open your browser to: **http://localhost:8000**

### Example Queries

**Weather Information:**
```
What's the weather in Tokyo?
How's the weather in Lagos, Nigeria?
Is it raining in London right now?
```

**Web Search:**
```
Search for latest AI developments
Find recent news about SpaceX launches
What are the top tech trends in 2025?
```

**General Conversation:**
```
Hello, how are you?
Tell me a joke
What can you help me with?
```

### Health Check Endpoints

```bash
# Check frontend health
curl http://localhost:8000/health

# Check MCP server health
curl http://localhost:5000/health

# List available tools
curl http://localhost:5000/tools
```

---

## 📁 Project Structure

```
mcp-agent/
│
├── .env                      # Environment variables (not in git)
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
├── README.md               # This file
│
├── mcp_server_http.py      # MCP tool server (HTTP-based)
│   ├── get_weather()       # Weather tool implementation
│   └── web_search()        # Web search tool implementation
│
├── app.py                  # Main frontend application
│   ├── Agent workflow      # LangGraph orchestration
│   ├── Flask routes        # API endpoints
│   └── SSE streaming       # Real-time updates
│
├── templates/
│   └── index.html          # Chat interface UI
│
└── tests/
    ├── test_tools.py       # Tool unit tests
    └── test_agent.py       # Agent workflow tests
```

---

## 📚 API Documentation

### Frontend API

#### POST /chat
Send a message to the agent.

**Request:**
```json
{
  "message": "What's the weather in Paris?",
  "session_id": "session_12345"
}
```

**Response:**
```json
{
  "status": "processing",
  "session_id": "session_12345"
}
```

#### GET /stream/{session_id}
Server-Sent Events stream for real-time updates.

**Event Types:**
- `status`: Processing status update
- `routing`: Tool selection reasoning
- `final`: Complete response

#### GET /health
System health check.

**Response:**
```json
{
  "status": "healthy",
  "frontend": "online",
  "mcp_server": "online",
  "groq_api": "configured"
}
```

### MCP Server API

#### POST /tools/call
Execute a tool.

**Request:**
```json
{
  "name": "get_weather",
  "arguments": {
    "city": "Tokyo"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "location": "Tokyo, Japan",
    "temperature": "15°C / 59°F",
    "condition": "Clear",
    "humidity": "65%"
  }
}
```

---

## 🔧 Development

### Adding New Tools

1. **Define tool in MCP server (mcp_server_http.py):**

```python
def calculate(expression: str):
    """Calculator tool"""
    try:
        result = eval(expression)  # Use safely in production!
        return {"success": True, "data": {"result": result}}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/tools/call', methods=['POST'])
def call_tool():
    # ... existing code ...
    elif tool_name == "calculate":
        expr = arguments.get("expression")
        return jsonify(calculate(expr))
```

2. **Update routing prompt in app.py:**

```python
routing_prompt = f"""
Available tools:
1. get_weather - Get weather for a city
2. web_search - Search the web
3. calculate - Perform math calculations  # NEW

User request: {state["msg"]}
"""
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
black app.py mcp_server_http.py

# Lint code
flake8 app.py mcp_server_http.py

# Type checking
mypy app.py
```

---

## 🌐 Deployment

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000 8000

CMD ["python", "app.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  mcp-server:
    build: .
    command: python mcp_server_http.py
    ports:
      - "5000:5000"
    env_file:
      - .env
  
  frontend:
    build: .
    command: python app.py
    ports:
      - "8000:8000"
    depends_on:
      - mcp-server
    env_file:
      - .env
```

### Production Considerations

- Use **Gunicorn** instead of Flask dev server
- Enable **HTTPS** with SSL certificates
- Implement **rate limiting** (Flask-Limiter)
- Add **authentication** (OAuth2, JWT)
- Use **Redis** for session management
- Deploy behind **NGINX** reverse proxy
- Monitor with **Prometheus** + **Grafana**

---

## 🐛 Troubleshooting

### Common Issues

**Issue: "GROQ_API_KEY not found"**
```bash
# Solution: Check .env file exists and has correct format
cat .env
# Should show: GROQ_API_KEY=gsk_...
```

**Issue: "MCP Server not responding"**
```bash
# Solution: Ensure server is running
curl http://localhost:5000/health

# If not running, check for port conflicts
netstat -an | grep 5000  # Windows: netstat -an | findstr 5000
```

**Issue: "Module not found"**
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Issue: "SSE connection timeout"**
```bash
# Solution: Check firewall settings and ensure both servers are running
# Increase timeout in app.py if needed
```

### Debug Mode

Enable detailed logging:

```python
# In app.py
import logging
logging.basicConfig(level=logging.DEBUG)

# In mcp_server_http.py
app.run(debug=True)
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide
- Add docstrings to all functions
- Write unit tests for new features
- Update README.md for significant changes

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Anthropic** - Model Context Protocol specification
- **Groq** - Free Llama 3.3 70B API access
- **Serper** - Web search API
- **wttr.in** - Weather data service
- **LangChain** - LangGraph workflow framework

---

## 📞 Contact

**Your Name** - [@yourtwitter](https://twitter.com/yourtwitter) - your.email@example.com

**Project Link**: https://github.com/yourusername/mcp-agent

---

## 🗺️ Roadmap

- [ ] Add conversation history/memory
- [ ] Implement user authentication
- [ ] Add more tools (calculator, translator, etc.)
- [ ] Create mobile app (React Native)
- [ ] Add voice input/output
- [ ] Multi-language support
- [ ] Webhook integrations (Slack, Discord)
- [ ] Analytics dashboard
- [ ] A/B testing framework
- [ ] Self-hosting guide for enterprise

---

**Built with ❤️ using MCP, Groq, and modern Python**