# backend/routers/__init__.py
from .chat import router as chat_router
from .upload import router as upload_router

__all__ = [
    "chat_router",
    "upload_router"
]
