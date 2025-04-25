# Reviewing the ElasticLM Agentic RAG Workflow

In this workshop you’ll explore how the ElasticLM app processes complex questions about company 10-Q reports using a *agentic Retrieval‑Augmented Generation (RAG)* system.

Unlike a basic RAG pipeline, this workflow plans, retrieves, and generates answers in discrete steps—much like a team of specialists collaborating on research.

This will help us ask questions like:
- `Compare revenue of FY25 Q1 and Q2 and when did Q2 end?`

# Core Concepts:
### Agent
- A self‑contained LLM function encapsulating a prompt and logic for a single step in the workflow (e.g. planning, retrieval, or generation).
- Receives structured input and returns structured output, making each step predictable and testable.
- Enables modular, interpretable pipelines by keeping responsibilities isolated.

### Model Context Protocol (MCP)
- An open standard by Anthropic for communication between LLMs and external tool servers.
- LLM sends a JSON request over stdio; the MCP server (e.g. Elasticsearch, web search) executes the operation and streams back JSON results.
- Simplifies AI integrations by providing a consistent interface for APIs, databases, and services.
- All tool servers live under `mcp_servers/` and can be extended with new capabilities.