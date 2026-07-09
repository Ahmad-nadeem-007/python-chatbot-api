# Knowledge Base endpoints: load data files into Chroma + test search
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.schemas import IngestResponse, SearchResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

# Path to the 'data' folder (inside the project root)
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


# 1. INGEST — read all .txt files in the data/ folder, create chunks, and load them into Chroma
@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents():
    try:
        if not DATA_DIR.exists():
            raise HTTPException(status_code=404, detail=f"data folder not found: {DATA_DIR}")

        # Remove old data so re-ingesting doesn't create duplicates
        rag_service.reset()

        files_processed = 0
        chunks_created = 0

        for file_path in DATA_DIR.glob("*.txt"):
            text = file_path.read_text(encoding="utf-8")
            chunks = rag_service.chunk_text(text)
            if chunks:
                rag_service.add_chunks(chunks, source=file_path.name)
                chunks_created += len(chunks)
            files_processed += 1

        return IngestResponse(
            status="success",
            files_processed=files_processed,
            chunks_created=chunks_created,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest error: {str(e)}")


# 2. SEARCH — for testing: which chunks come up for a given question?
@router.get("/search", response_model=SearchResponse)
async def search_knowledge(q: str):
    try:
        # max_distance=None → show all top chunks with their scores (no filter)
        results = rag_service.search(q, top_k=3, max_distance=None)
        return SearchResponse(query=q, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
