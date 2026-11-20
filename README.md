# PUCIT BS(CS) CGPA Guider — Assignment 3

An AI-powered GPA and CGPA assistant for PUCIT BS(CS) students upgraded with **persistent SQLite memory**, **real-time streaming**, **remote MCP tool hosting**, and **graceful downtime handling**.

---

## Submission Details

* **MCP Server URL:** `https://pucit-academic-mcp.fastmcp.app/mcp`
* **MCP Server API Key:** `https://pucit-academic-mcp.fastmcp.app/mcp`
* **GitHub Repository (Server Code):** https://github.com/SomanAbbasi/pucit-academic-mcp[cite: 3]

---

## Project Structure

```text
BCSF24M014_Assignment3/
├── server/
│   ├── server.py          # FastMCP server exposing all 7 CGPA tools
│   ├── tools.py           # Plain Python functions for GPA/CGPA & PUCIT courses
│   └── requirements.txt   # Server dependencies
├── agent/
│   ├── agent.py           # Async LangChain agent with MCPAdapter, SQLite memory & streaming
│   ├── llm.py             # Groq LLM initialization
│   └── .env               # API keys and MCP server URL (not committed to GitHub)
└── README.md