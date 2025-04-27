# backend/workflows/upload_graph.py

import pickle
import msgpack
from typing import TypedDict, Optional, Literal, List, Dict, Any
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from utils.logger import logger
from asyncio import Semaphore
import asyncio
from clients.elasticsearch_client import es
from fastapi import HTTPException
from datetime import datetime
from uuid import uuid4

# The UploadState now stores the parsed elements as a list of dictionaries.
class UploadState(TypedDict, total=False):
    user_id: str
    file_name: str
    file_content: bytes
    chunks: List[Dict[str, Any]]    # Each parsed element is a dict.
    status: str
    summary_indexed: str
    overall_summary: str
    summary_message: str

async def index_chunks(user_id: str, file_name: str, chunks: list, doc_type: str = 'parsed') -> int:
    """
    Indexes each parsed element directly into Elasticsearch.
    The parsed element (a dictionary) is augmented with metadata and indexed.
    """
    index_name = f"elastic_lm_docs"
    documents = []
    for chunk in chunks:
        document = chunk.copy()
        document["user_id"] = user_id
        document["file_name"] = file_name
        document["indexed_at"] = datetime.utcnow().isoformat()
        document["doc_type"] = doc_type
        doc_id = document.get("element_id") or str(uuid4())
        action = {"_index": index_name, "_id": doc_id}
        action.update(document)
        documents.append(action)
    try:
        from elasticsearch.helpers import async_bulk
        success_count, errors = await async_bulk(
            es,
            documents,
            raise_on_error=False,
            raise_on_exception=False,
            timeout="120s"
        )
        logger.debug(f"Successfully indexed bulk into '{index_name}'.")
        if errors:
            for error in errors:
                logger.error(f"Indexing error: {error}")
        return success_count
    except Exception as e:
        logger.error(f"Error during bulk indexing into '{index_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error indexing documents.")

async def parse_node(state: UploadState, config: dict) -> UploadState:
    from services.parser_service import parse_document
    try:
        logger.debug(
            f"Parsing the uploaded document for user: {state['user_id']} and file: {state['file_name']}."
        )
        # Call the parser to get the list of elements.
        chunks = await parse_document(state["file_content"], state["file_name"])
        if not chunks:
            logger.error("No chunks parsed from the document.")
            state["status"] = "parse_error"
            raise Exception("Failed to parse document: No content extracted.")
        state["chunks"] = chunks
        state["status"] = "parsed"
        logger.debug(f"Parsed {len(chunks)} chunks from the document.")
        return state
    except Exception as e:
        logger.error(f"Error in parse_node: {e}")
        state["status"] = "parse_error"
        raise Exception(f"Error parsing document: {e}")

async def index_node(state: UploadState, config: dict) -> UploadState:
    try:
        logger.debug(f"Indexing the parsed chunks for user: {state['user_id']} and file: {state['file_name']}.")
        semaphore = Semaphore(16)  # Allow 16 chunks at a time
        async def rate_limited_index(chunk):
            async with semaphore:
                count = await index_chunks(state["user_id"], state["file_name"], [chunk], 'parsed')
                await asyncio.sleep(0.2)  # Enforce delay per chunk
                return count
        success_count = sum(await asyncio.gather(*[rate_limited_index(chunk) for chunk in state["chunks"]]))
        if success_count > 0:
            state["status"] = "success"
            logger.debug("Indexing completed successfully.")
        else:
            state["status"] = "index_error"
            logger.error("Indexing failed: No documents were indexed.")
            raise Exception("Failed to index any documents.")
        if "file_content" in state:
            del state["file_content"]
            logger.debug("Removed 'file_content' from state.")
        return state
    except Exception as e:
        logger.error(f"Error in index_node: {e}")
        state["status"] = "index_error"
        raise Exception(f"Error indexing documents: {e}")

def build_summary_prompt(filename: str, page_number: int, page_text: str) -> str:
    if page_number != 0:
        prompt = f"""
        You are a knowledgeable assistant tasked with summarizing text from user-uploaded documents.
        Below is the text from a single page of a document. Your goal is to create a concise and precise summary that:
        1. Captures the key points and main ideas of the page.
        2. Supports the creation of an overall summary for the full document.
        3. Aids in retrieving relevant documents from Elasticsearch for future user queries.

        Constraints:
        - Keep the summary between 50-100 words.
        - Focus on the most important details, avoiding trivial or redundant information.
        - Do not include any additional information, explanations, or commentary.
        - Reply with **ONLY** the summary text as a single paragraph.

        Filename: {filename}
        Page number: {page_number}
        Page text: {page_text}

        Output the summary in an easily readable structure. You can use line breaks and short paragraphs. 
        Ideally there will be a list of key bullet points if it makes sense with the summarised content. 
        """
    else:
        prompt = f"""
        You are a knowledgeable assistant tasked with creating a concise summary of an entire document.
        Below are summaries generated for each page of the document. Your job is to synthesize these individual summaries into 
        a clear and cohesive overall summary.

        Constraints:
        - Keep the overall summary between 100-500 words.
        - Identify recurring themes, key points, or important details from across the pages.
        - Do not include any additional information, explanations, or commentary.
        - Reply with **ONLY** the summary text as a single paragraph.

        Filename: {filename}
        Page Summaries: {page_text}
       
        Output the overall summary in an easily readable structure. You can use line breaks and short paragraphs. 
        Ideally there will be a list of key bullet points if it makes sense with the summarised content. 

        """
    return prompt

async def summarize_node(state: UploadState, config: dict) -> UploadState:
    from clients.llm_client import call_llm
    from collections import defaultdict
    import asyncio

    generate_summary = True  # Change this as needed (e.g., a UI flag)
    if generate_summary:
        try:
            # Group chunks by page using the page number in metadata.
            grouped_chunks = defaultdict(list)
            for chunk in state["chunks"]:
                page_number = chunk.get("metadata", {}).get("page_number", 0)
                text = chunk.get("text", "")
                logger.debug(f"Chunk (page {page_number}): {text[:50]}...")
                grouped_chunks[page_number].append(text)

            # Create tasks for summarizing each page concurrently.
            summary_tasks = []
            for page_number, texts in grouped_chunks.items():
                page_text = " ".join(texts)
                prompt = build_summary_prompt(state["file_name"], page_number, page_text)
                summary_tasks.append(asyncio.create_task(call_llm(prompt)))

            summaries_results = await asyncio.gather(*summary_tasks)

            summaries = []
            for i, summary in enumerate(summaries_results):
                summaries.append({
                    "page_number": list(grouped_chunks.keys())[i],
                    "summary": summary.strip()
                })

            # Combine page summaries to build an overall summary.
            all_summaries_text = " ".join([s["summary"] for s in summaries])
            overall_summary_prompt = build_summary_prompt(state["file_name"], page_number=0,
                                                          page_text=all_summaries_text)
            overall = {"page_number": 0, "summary": await call_llm(overall_summary_prompt)}
            state["overall_summary"] = overall["summary"]
            summaries.append(overall)

            # Optionally index the summaries.
            success_count = await index_chunks(state["user_id"], state["file_name"], summaries, 'summary')
            if success_count > 0:
                state["summary_indexed"] = "success"
                logger.debug("Indexing summary completed successfully.")
            else:
                state["summary_indexed"] = "index_error"
                logger.error("Indexing failed: No documents were indexed.")
                raise Exception("Failed to index any summary documents.")
            return state
        except Exception as e:
            logger.error(f"Error in summarize_node: {e}")
            state["status"] = "parse_error"
            raise Exception(f"Error summarizing document: {e}")
    else:
        state["summary_indexed"] = "skipped"
        return state


async def end_cleaner(state: UploadState, config: dict) -> UploadState:
    """
    Final node that prepares the response for the UI, including the summary.
    """
    logger.debug("Ending the upload workflow.")
    if "overall_summary" in state:
        summary_message = (
            f"### {state['file_name']} has been successfully uploaded.\n\n"
            f"**Overall summary:**\n\n"
            f"{state['overall_summary']}\n\n"
            "Feel free to ask any follow-up questions."
        )
        state["summary_message"] = summary_message
        logger.debug(f"Generated UI message: {summary_message}")
    else:
        logger.warning(f"Overall summary missing for file: {state['file_name']}")
    return state

# Define the workflow.
upload_workflow = StateGraph(UploadState)
upload_workflow.add_node("parse", parse_node)
upload_workflow.add_node("index", index_node)
upload_workflow.add_node("summarize", summarize_node)
upload_workflow.add_node("end_cleaner", end_cleaner)

upload_workflow.add_edge(START, "parse")
upload_workflow.add_edge("parse", "index")
upload_workflow.add_edge("index", "summarize")
upload_workflow.add_edge("summarize", "end_cleaner")
upload_workflow.add_edge("end_cleaner", END)

# Initialize the MemorySaver Checkpointer and compile the workflow.
from langgraph.checkpoint.memory import MemorySaver
upload_checkpointer = MemorySaver()
upload_app = upload_workflow.compile(checkpointer=upload_checkpointer)
