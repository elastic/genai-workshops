import os
import asyncio
from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
# from langchain_openai import AzureChatOpenAI
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    history: list[str] = []

async def run_agent_with_query(query: str, history: list[str] = []) -> str:
    client = MCPClient.from_config_file("backend/elasticsearch_mcp.json")

    # llm = AzureChatOpenAI(
    #     openai_api_version="2025-01-01-preview",
    #     azure_deployment="gpt-4o",
    #     azure_endpoint="https://litellm-proxy-service-1059491012611.us-central1.run.app/v1/chat/completions",
    #     # azure_endpoint="https://",
    #     api_key=os.getenv("AZURE_OPENAI_API_KEY")
    # )

    llm = ChatOpenAI(
        model="gpt-4o",  # Corresponds to azure_deployment
        # Set base_url to the root of your LiteLLM proxy.
        # The OpenAI client will append /v1/chat/completions etc.
        base_url=os.getenv("LLM_PROXY_URL"),
        openai_api_key=os.getenv("LLm_API_KEY")
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
    )

    agent = MCPAgent(llm=llm, client=client, max_steps=30, system_prompt=system_prompt)

    full_prompt = "\n".join(history + [query])

    try:
        return await agent.run(full_prompt)
    finally:
        await client.close_all_sessions()

@app.post("/api/books-chat")
async def books_chat_endpoint(req: ChatRequest):
    response = await run_agent_with_query(req.query, req.history)
    return { "response": response }

@app.get("/")
async def root():
    return { "message": "ES Book server is running." }

