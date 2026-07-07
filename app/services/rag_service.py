# RAG ka dimaag (Chroma version): text todna, store karna, aur relevant chunks dhoondna
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

# Chroma apna data yahan (local folder mein) save karega
CHROMA_DIR = Path(__file__).resolve().parents[2] / "chroma_db"

# Hybrid mode ki limit: is se zyada "distance" (kamzor match) wale chunks chhod diye jayenge.
# cosine distance: 0 = bilkul milta, 1 = bilkul nahi milta. 0.75 ek theek-thaak limit hai.
RELEVANCE_THRESHOLD = 0.75


class RAGService:
    def __init__(self):
        # Local vector database (file-based, koi server/extension nahi chahiye)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))

        # Embedding model: text ko numbers mein badalta hai (free/local, all-MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # "knowledge_base" naam ka collection (jaise ek table) — agar nahi hai to bana do
        # hnsw:space=cosine → match ka score saaf 0..1 range mein milta hai
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # Bara text ko chote chunks mein todta hai (thoda overlap taake matlab na tootay)
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start += chunk_size - overlap  # thoda peeche jao taake overlap rahe
        return chunks

    # Purana data saaf karo (dobara ingest par duplicate na banein)
    def reset(self):
        self.client.delete_collection("knowledge_base")
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # Chunks ko Chroma mein daalo (embedding Chroma khud bana leta hai)
    def add_chunks(self, chunks: list[str], source: str):
        ids = [f"{source}-{i}" for i in range(len(chunks))]
        metadatas = [{"source": source} for _ in chunks]
        self.collection.add(documents=chunks, ids=ids, metadatas=metadatas)

    # User ke sawal se milte-julte top chunks nikalo.
    # max_distance = limit: is se zyada door (kamzor match) wale chunks chhod diye jayenge.
    # max_distance=None → sab dikhao (test/calibration ke liye).
    def search(self, query: str, top_k: int = 3, max_distance: float | None = RELEVANCE_THRESHOLD) -> list[dict]:
        results = self.collection.query(query_texts=[query], n_results=top_k)
        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        items = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            # Hybrid mode: kamzor match (limit se door) skip karo
            if max_distance is not None and dist > max_distance:
                continue
            items.append({
                "content": doc,
                "source": meta.get("source", ""),
                "distance": round(dist, 4),
            })
        return items


rag_service = RAGService()
