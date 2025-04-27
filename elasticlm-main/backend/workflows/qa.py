"""
Agentic QA Workflow Module

This module defines a minimal synchronous workflow for processing QA tasks
with company quarterly report data. It simplifies the process to planning, querying,
and generating answers using prompt files.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from clients.llm_client import call_llm
from config import DEFAULT_INDEX, settings
from utils.helpers import load_prompts
from mcp_servers import *
from utils.logger import logger

# ===== Prompts =====

PROMPTS = load_prompts()
PLANNER_PROMPT = PROMPTS["planner"]
GENERATOR_PROMPT = PROMPTS["generate"]

# ===== Agents =====

async def planner_agent(question: str) -> list[dict]:
    """Generate a plan for the given question using the planner prompt."""
    # Agent function: plan_question uses LLM to generate a structured plan
    logger.debug(f"Planning question: {question}")
    prompt = PLANNER_PROMPT + f"\nUser question: {question}"
    response = await call_llm(prompt)
    return json.loads(response).get('steps', [])


async def generate_agent(question: str, context: list[dict]) -> str:
    """Generate an answer using the generator prompt and retrieved chunks."""
    logger.debug(f"Generating answer for question: {question}")
    # Agent function: generate_answer uses LLM with context to produce the final answer
    prompt = GENERATOR_PROMPT + f"\nQuestion: {question}\nContext:\n{context}"
    return await call_llm(prompt)

# ===== Flow runner =====

async def run_qa(question: str) -> str:
    """Run the QA workflow for the given question."""
    # Flow runner: orchestrates the use of agent functions and tool calls to produce an answer
    try:
        steps = await planner_agent(question)
        query_logs: list[str] = []
        results = []    # Initialize results with a default value
        for step in steps:
            if step.get('action') == 'query_elasticsearch':
                # Tool execution: querying Elasticsearch as part of the plan
                args = step.get('args', {})
                # Extract a human-readable search term from the DSL
                query = args.get('query', {})
                semantic_q = query['retriever']['standard']['query']['bool']['should'][0]['semantic']['query']
                query_logs.append(f"- [**ES Search**]: '{semantic_q}'")
                # Search in ES
                # Call the elastic_mcp server to perform the search
                hits = await elastic_mcp.call(
                    "search",
                    index=DEFAULT_INDEX,
                    queryBody=query,
                )
                if not 'Total results: 0' in hits[0].text:
                    results.extend(hits)
                else:
                    # If no hits, log the event
                    query_logs.append(f"- [**ES Search**]: No results found for '{semantic_q}'")
                    ## >> Add web search tool here <<
        # Generate the final answer
        answer = await generate_agent(question, results)
        # Combine tool usage logs and agent-generated answer
        log_section = "\n".join(query_logs)
        return f"{log_section}\n --- \n{answer}"
    except Exception as e:
        # Agent error handling: report exceptions
        return f"Error: {e}"