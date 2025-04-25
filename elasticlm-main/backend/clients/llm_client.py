# backend/clients/llm_client.py

import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from openai import OpenAIError
from utils.logger import logger
from openai import AsyncAzureOpenAI
from config import settings
import re

AZURE_OPENAI_DEPLOYMENT_NAME = settings.AZURE_OPENAI_DEPLOYMENT_NAME

client = AsyncAzureOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_version=settings.AZURE_OPENAI_API_VERSION,
)

logger.info("AsyncAzureOpenAI client initialized.")

async def call_llm(prompt: str) -> str:
    """
    Sends a prompt to the LLM and returns the completion as a string.
    """
    system_instructions = (
        "You are part of a knowledge Q&A system. Follow the user prompts."
    )

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": prompt}
    ]

    try:
        logger.debug(f"Calling LLM")
        response = await client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=messages,
            stream=False
        )

        # Log only the first part of the assistant content, not the full response object
        logger.debug(f"Content snippet: {response.choices[0].message.content[:50]}...")
        # Clean up whitespace and excessive newlines
        raw = response.choices[0].message.content

        return raw

    except Exception as e:
        logger.exception("Error during LLM simple call.")
        raise