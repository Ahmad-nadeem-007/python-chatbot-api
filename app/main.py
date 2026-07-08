from fastapi import FastAPI
from app.database import engine, Base
# 1. CHANGE: 'chat' ki jagah direct 'chat_router' import karen
from app.routers import chat_router, knowledge_router

app = FastAPI(
    title="Knowledge Base Chatbot API (Groq)",
    description="FastAPI chatbot with async PostgreSQL & Groq (Llama 3.3 70B)",
    version="1.0"
)

# Startup event tables auto create karne ke liye
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Create tables if they do not exist
        await conn.run_sync(Base.metadata.create_all)

# 2. CHANGE: 'chat.router' ki jagah 'chat_router' likhen
app.include_router(chat_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Chatbot server is up and running. Visit /docs for Swagger UI."}