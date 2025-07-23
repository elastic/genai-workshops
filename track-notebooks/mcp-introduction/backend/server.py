# In backend/server.py

import logging
import sys
import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.callbacks import BaseCallbackHandler
from typing import AsyncIterable, Optional, List, Any, Dict

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger(__name__)


class ToolCallbackHandler(BaseCallbackHandler):
    """A custom callback handler to record which tools are used."""
    def __init__(self):
        super().__init__()
        self.used_tools = []

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Called when the agent is about to start using a tool."""
        tool_name = serialized.get("name")
        logger.info(f"Agent is using tool: {tool_name}")
        self.used_tools.append(tool_name)


load_dotenv()
logger.info("Dotenv loaded successfully.")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured.")

class ChatRequest(BaseModel):
    query: str
    history: list[str] = []

async def run_agent_with_query(query: str, history: list[str] = []) -> str:

    mcp_client = MCPClient.from_config_file("backend/elasticsearch_mcp.json")
    raw_proxy_url = os.getenv("PROXY_URL")
    llm_api_key = os.getenv("PROXY_API_KEY")
    unneeded_path = "/v1/chat/completions"
    llm_base_url = raw_proxy_url
    if llm_base_url and llm_base_url.endswith(unneeded_path):
        llm_base_url = llm_base_url.removesuffix(unneeded_path)
        logger.info(f"PROXY_URL was trimmed to: {llm_base_url}")

    llm = ChatOpenAI(
        model="gpt-4o",
        base_url=llm_base_url,
        openai_api_key=llm_api_key
    )


    system_prompt = (
        "You are a helpful and knowledgeable librarian, equipped with tools to assist users with their book inquiries. " +
        "You have access to the Elastic MCP server with the 'books' index, and the Google Books API for purchase information. " +
        "Your available tools are:\n" +
        "- **search**: Use this tool to find general information about books within the 'books' Elasticsearch index. When using this tool, you MUST provide both `index` (which should be 'books') and a valid Elasticsearch `queryBody` (e.g., using a `match` query, `bool` query, etc.). Remove any case formatting in the query body. Never return more than 5 results at any one time and always present the results in a human readable way. You can bold the title. \n" +
        "- **search_google_books**: Use this tool when a user explicitly asks about purchasing a book, where to buy it, its price, or general sales availability. Provide the `title` of the book, and optionally the `author` if known.\n" +
        "- **list_indices**, **get_mappings**, **get_shards**: (Not usually needed—only if the user explicitly requests low-level Elasticsearch details.)\n\n" +
        "**Important formatting rule:**"
        "1. Render each book as its own numbered card or entry."
        "2. **Any text that isn’t part of a specific book entry**—for example, a final wrap-up, recommendation, or “next steps” paragraph—**must begin with the header**:"
        "Additional Notes:"
        "and then that text.  Do not include that under any numbered item or card."
        "After using a tool, begin your answer with “Using the [tool_name] tool, …” etc."
        "After retrieving information using any tool, explain the results clearly and engagingly, like a human librarian would:\n" +
        "- Compare or contrast books clearly, if multiple are found.\n" +
        "- Highlight themes, readability, or significance of the books.\n" +
        "- Format your responses so they're easy to read and inviting.\n" +
        "- Avoid just listing raw fields; interpret the data for the user.\n" +
        "- It's okay to express a gentle opinion or help guide the user to their next read.\n" +
        "- Speak naturally, like you're helping a curious reader at the reference desk.\n\n" +
        "If multiple books are found by any tool, summarize each one clearly in plain English.\n\n" +
        "After using a tool, you MUST begin your final answer with **'Using the [tool_name] tool, '** where [tool_name] is exactly the tool you invoked (for example, 'Using the search tool, I found…'). " +
        "If you did not use a tool, just answer directly."
        )

    agent = MCPAgent(llm=llm, client=mcp_client, max_steps=30, system_prompt=system_prompt)

    full_prompt = "\n".join(history + [query])

    try:
        return await agent.run(full_prompt)
    finally:
        await mcp_client.close_all_sessions()



@app.post("/api/books-chat")
async def books_chat_endpoint(req: ChatRequest, http_request: Request):
    # logger.info(f"INCOMING HEADERS: {dict(http_request.headers)}")
    try:
        response = await run_agent_with_query(req.query, req.history)
        return {"response": response}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

@app.get("/")
async def root():
    logger.info("Root endpoint '/' accessed.")
    return {"message": "ES Book server is running."}


