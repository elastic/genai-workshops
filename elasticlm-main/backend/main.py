# backend/main.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routers import chat_router, upload_router
from config import Settings
from clients.elasticsearch_client import es, initialize_indices
from workflows import upload_app
from langgraph_sdk import get_client, get_sync_client
from utils.logger import logger
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from mcp_servers import get_servers
import asyncio

app = FastAPI(title="Elastic LM")
settings = Settings()

origins = [
    "http://localhost:3000",
    "https://your-frontend-domain.com",
    "https://smith.langchain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def global_exception_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except HTTPException as he:
        return JSONResponse(status_code=he.status_code, content={"detail": he.detail})
    except RequestValidationError as ve:
        return JSONResponse(status_code=422, content={"detail": ve.errors()})
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

app.include_router(upload_router, prefix="/upload", tags=["Upload"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])

@app.get("/health", summary="Health Check")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    await asyncio.gather(*(srv.start() for srv in get_servers()))
    logger.debug(f"Elasticsearch URL: {settings.ES_URL}")
    try:
        await initialize_indices()
        is_alive = await es.ping()
        if is_alive:
            logger.info("Successfully connected to Elasticsearch.")
        else:
            logger.error("Failed to connect to Elasticsearch.")
    except Exception as e:
        logger.error(f"Elasticsearch connection error: {e}")

    if settings.OTEL_ENABLED:
        setup_tracing(app)

    client = get_client(url="http://localhost:2024")
    sync_client = get_sync_client(url="http://localhost:2024")

    try:
        await upload_app.ainvoke(
            {},
            config={"configurable": {"thread_id": "startup_test"}}
        )
        logger.info("Successfully registered upload_graph with LangGraph server.")
    except Exception as e:
        logger.error(f"Failed to register workflows with LangGraph server: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await es.close()
    await asyncio.gather(*(srv.stop() for srv in get_servers()))
    logger.info("Elasticsearch client closed.")
