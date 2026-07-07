# Knowledge Base endpoints: data files ko Chroma mein daalna + search test karna
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.schemas import IngestResponse, SearchResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

# 'data' folder ka path (project root ke andar)
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


# 1. INGEST — data/ folder ki saari .txt files parho, chunks banao, Chroma mein daal do
@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents():
    try:
        if not DATA_DIR.exists():
            raise HTTPException(status_code=404, detail=f"data folder nahi mila: {DATA_DIR}")

        # Purana data hata do taake dobara ingest par duplicate na banein
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


# 2. SEARCH — test ke liye: kisi sawal par kaun se chunks aate hain?
@router.get("/search", response_model=SearchResponse)
async def search_knowledge(q: str):
    try:
        # max_distance=None → saare top chunks score ke saath dikhao (koi filter nahi)
        results = rag_service.search(q, top_k=3, max_distance=None)
        return SearchResponse(query=q, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
