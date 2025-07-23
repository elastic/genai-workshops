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
    raw_proxy_url = os.getenv("PROXY_URL") or os.getenv("LLM_PROXY_URL")
    llm_api_key = os.getenv("PROXY_API_KEY") or os.getenv("LLM_APIKEY")
    unneeded_path = "/v1/chat/completions"
    llm_base_url = raw_proxy_url
    if llm_base_url and llm_base_url.endswith(unneeded_path):
        llm_base_url = llm_base_url.removesuffix(unneeded_path)
        logger.info(f"PROXY_URL was trimmed to: {llm_base_url}")

    if not llm_base_url.startswith("https://"):
        llm_base_url = "https://" + llm_base_url
        logger.info(f"Prepended 'https://' to PROXY_URL: {llm_base_url}")

    logger.info(f"llm_base_url: {llm_base_url}")


    llm = ChatOpenAI(
        model="gpt-4o",
        base_url=llm_base_url,
        openai_api_key=llm_api_key
    )


    system_prompt = (
        "You are using the Elastic MCP server with access to the 'books' index. "
        "You are answering questions from a user. "
        "When using the 'search' tool, provide both `index` and `queryBody`. "
        "After retrieving books, explain results like a human librarian might:\n"
        "- Compare or contrast books clearly\n"
        "- Highlight themes, readability, or significance\n"
        "- Format your responses so they're easy to read\n"
        "- Avoid just listing raw fields\n"
        "- It's okay to express an opinion or help guide the user\n"
        "- Speak naturally, like you're helping a curious reader\n"
        "If multiple books are found, summarize each one clearly in plain English."
         "After using a tool, you MUST begin your final answer to the user with the phrase 'Using the [tool_name] tool, ' where [tool_name] is the exact name of the tool you used. For example: 'Using the search tool, I found that...'. If you did not use a tool, just answer directly.\n\n"

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


