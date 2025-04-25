# backend/routers/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi.responses import StreamingResponse
from utils.logger import logger
import uuid
from workflows.qa import run_qa

router = APIRouter(tags=["Chat"])

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    customPrompt: str = ""
    enableCaching: bool = False
    similarityThreshold: int = 50
    ignoreCache: bool = False
    selectedSources: List[str] = []

@router.post("/", summary="Chat endpoint (streams final text only)")
async def chat_endpoint(req: ChatRequest):
    logger.debug(f"Received chat request body: {req.json()[:50]}")
    if not req.messages:
        logger.warning(f"Empty message list.")
        raise HTTPException(status_code=400, detail="No messages provided")
    question = req.messages[-1].content
    logger.debug(f"User asked: {question}")
    chat_id = str(uuid.uuid4())
    logger.debug(f"Generated chat_id: {chat_id}")
    try:
        # Directly run the simplified QA pipeline in the current event loop
        final_text = await run_qa(question)
        async def chunked_text(text: str, size=60):
            start = 0
            while start < len(text):
                yield text[start:start+size]
                start += size
        return StreamingResponse(chunked_text(final_text), media_type="text/event-stream")
    except HTTPException as he:
        logger.error("Error processing chat request.", exc_info=he)
        raise
    except Exception as e:
        logger.error("Error processing chat request.", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
