# app/routers/__init__.py

from .chat import router as chat_router
from .knowledge import router as knowledge_router

# This lets main.py import chat_router and knowledge_router directly
