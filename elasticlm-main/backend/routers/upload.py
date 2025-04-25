# backend/routers/upload.py

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from workflows.upload_graph import upload_app
from clients.elasticsearch_client import create_user_docs_index
from utils.logger import logger
import uuid
from typing import Optional

# In-memory status store (for demo purposes; replace with persistent storage in production)
status_store = {}

router = APIRouter()

@router.post("/", summary="Upload a file")
async def upload_file(file: UploadFile = File(..., description="The file to upload")):
    try:
        thread_id = str(uuid.uuid4())
        file_content = await file.read()
        await create_user_docs_index()
        initial_state = {
            "user_id": None,
            "file_name": file.filename,
            "file_content": file_content,
            "chunks": [],
            "status": "pending"
        }
        # Mark as pending
        status_store[file.filename] = {"status": "pending", "summary_message": None}
        config = {"configurable": {"thread_id": thread_id}}
        final_state = await upload_app.ainvoke(initial_state, config=config)
        if final_state.get("status") != "success":
            logger.error(f"Upload graph failed for file: {file.filename}")
            status_store[file.filename] = {"status": "error", "summary_message": None, "detail": "Failed to process the uploaded file."}
            raise Exception("Failed to process the uploaded file.")
        # Mark as done
        status_store[file.filename] = {"status": "done", "summary_message": final_state.get('summary_message')}
        return {"summary_message": final_state['summary_message']}
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}")
        status_store[file.filename] = {"status": "error", "summary_message": None, "detail": str(e)}
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            await file.close()
            logger.debug(f"Closed UploadFile object for file: {file.filename}")
        except Exception as close_error:
            logger.error(f"Error closing file: {close_error}")

@router.get("/status", summary="Get upload status")
async def get_upload_status(filename: str = Query(..., description="The name of the uploaded file")):
    status = status_store.get(filename)
    if not status:
        return JSONResponse(status_code=404, content={"status": "not_found", "detail": "No status found for this file."})
    return status
