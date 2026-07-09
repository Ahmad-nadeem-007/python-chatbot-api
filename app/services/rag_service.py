# The brain of RAG (Chroma version): split text, store it, and find relevant chunks
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

# Chroma will save its data here (in a local folder)
CHROMA_DIR = Path(__file__).resolve().parents[2] / "chroma_db"

# Hybrid mode limit: chunks with a "distance" greater than this (weak match) will be dropped.
# cosine distance: 0 = perfect match, 1 = no match at all. 0.75 is a reasonable limit.
RELEVANCE_THRESHOLD = 0.75


class RAGService:
    def __init__(self):
        # Local vector database (file-based, no server/extension required)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))

        # Embedding model: converts text into numbers (free/local, all-MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # A collection named "knowledge_base" (like a table) — create it if it doesn't exist
        # hnsw:space=cosine → the match score comes out cleanly in the 0..1 range
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # Splits large text into small chunks (with a little overlap so the meaning isn't broken)
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start += chunk_size - overlap  # step back a little so there is overlap
        return chunks

    # Clear old data (so re-ingesting doesn't create duplicates)
    def reset(self):
        self.client.delete_collection("knowledge_base")
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # Add chunks into Chroma (Chroma generates the embeddings itself)
    def add_chunks(self, chunks: list[str], source: str):
        ids = [f"{source}-{i}" for i in range(len(chunks))]
        metadatas = [{"source": source} for _ in chunks]
        self.collection.add(documents=chunks, ids=ids, metadatas=metadatas)

    # Fetch the top chunks most similar to the user's question.
    # max_distance = limit: chunks farther than this (weak match) will be dropped.
    # max_distance=None → show everything (for testing/calibration).
    def search(self, query: str, top_k: int = 3, max_distance: float | None = RELEVANCE_THRESHOLD) -> list[dict]:
        results = self.collection.query(query_texts=[query], n_results=top_k)
        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        items = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            # Hybrid mode: skip weak matches (farther than the limit)
            if max_distance is not None and dist > max_distance:
                continue
            items.append({
                "content": doc,
                "source": meta.get("source", ""),
                "distance": round(dist, 4),
            })
        return items


rag_service = RAGService()
