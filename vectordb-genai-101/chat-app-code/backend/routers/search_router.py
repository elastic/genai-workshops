import os
import logging
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services import search_service, inference_service, llm_service
from fastapi import WebSocket, APIRouter
from starlette.websockets import WebSocketDisconnect

router = APIRouter()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Set this to True to stream LLM responses back to the client
# Streaming not implemented in this version
# streaming_llm = False

class SearchQuery(BaseModel):
    query: str
    context_type: str


@router.post("/search")
async def perform_search(search_query: SearchQuery):
    logging.info(f"Received query: {search_query.query}")
    try:
        prompt_context = search_service.semantic_search(search_query.query, search_query.context_type)
        llm_response = bedrock_service.query_aws_bedrock(prompt_context)
        return {"prompt": prompt_context, "llm_response": llm_response}
    except Exception as e:
        logging.error(f"Error in processing search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ChatMessage(BaseModel):
    message: str


MAX_CHUNK_SIZE = 4000
async def send_large_text(websocket, text, msg_type="verbose_info"):
    for i in range(0, len(text), MAX_CHUNK_SIZE):
        await websocket.send_json({
            "type": msg_type,
            "chunk_index": i // MAX_CHUNK_SIZE,
            "is_final_chunk": (i + MAX_CHUNK_SIZE) >= len(text),
            "text": text[i:i + MAX_CHUNK_SIZE],
        })


def build_readable_context(hits):
    output = ""
    for hit in hits:
        output += f"{str(hit)}\n\n"
    return output


@router.websocket_route("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    convo_history = llm_service.init_conversation_history()

    try:
        while True:
            data = await websocket.receive_text()
            chat_message = ChatMessage.parse_raw(data)
            logging.info(f"Received message: {chat_message.message}")

            query = chat_message.message

            try:
                # Step 1: Search Elasticsearch (in thread)
                context_hits = await asyncio.to_thread(
                    search_service.perform_es_search,
                    query,
                    "nyc_regulations"
                )

                # Step 2: Build prompt
                prompt = llm_service.create_llm_prompt(
                    query,
                    context_hits,
                    convo_history
                )

                # Step 3: Send back context to frontend (optional)
                # context_str = build_readable_context(context_hits)
                # await send_large_text(websocket, context_str, msg_type="verbose_info")

                # Step 4: LLM Inference with retry
                try:
                    llm_response = await asyncio.to_thread(
                        inference_service.es_chat_completion,
                        prompt,
                        os.getenv("INFERENCE_ID")
                    )
                except Exception as e:
                    logging.warning(f"LLM call failed after retries: {e}")
                    llm_response = (
                        "Sorry, I'm having trouble reaching the AI model right now. "
                        "Please try again shortly."
                    )

                # Step 5: Send full response to UI
                await websocket.send_json({
                    "type": "full_response",
                    "text": llm_response
                })

                # Step 6: Update conversation history
                convo_history = llm_service.build_conversation_history(
                    history=convo_history,
                    user_message=query,
                    ai_response=llm_response
                )

            except Exception as inner_e:
                logging.exception(f"Error during chat cycle: {inner_e}")
                await websocket.send_json({
                    "type": "error_message",
                    "text": f"Unexpected error: {str(inner_e)}"
                })

    except WebSocketDisconnect as e:
        logging.warning(f"WebSocket disconnected: {e.code}")
    except Exception as e:
        logging.exception("WebSocket encountered an unexpected error")
        try:
            await websocket.send_json({
                "type": "error_message",
                "text": "An unexpected error occurred. Connection will close."
            })
            await websocket.close(code=1011)
        except RuntimeError:
            logging.debug("WebSocket already closed. Skipping close.")
