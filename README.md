# 🤖 FastAPI Chatbot API — with RAG (Groq + Llama 3.3 + ChromaDB)

An **AI chatbot backend** built with **FastAPI**, using an **async PostgreSQL** database and **Groq (Llama 3.3 70B)** for AI responses. On top of the basic chatbot, it also has a **RAG (Retrieval-Augmented Generation)** layer: the bot can answer questions from a **custom knowledge base** using **embeddings + vector search (ChromaDB)** — instead of just guessing.

Chat sessions and messages are stored in PostgreSQL, the knowledge base lives in a local ChromaDB vector store, and the entire API was tested in the browser using Swagger UI.

---

## 📌 What This Project Does

**Core chatbot:**
- User sends a message → the backend saves it in the database
- The AI (Llama 3.3) replies using the previous chat history as context
- The bot's reply is also saved in the database
- The user can view a **list** of all their chats
- The user can fetch the full **history of any chat (with pagination)**
- The user can **delete** a chat (all its messages are deleted via cascade)

**RAG / Knowledge Base (the interesting part):**
- Custom documents (company docs, FAQs, policies) are broken into **chunks** and turned into **embeddings**, then stored in **ChromaDB**
- When a user asks something, the backend runs a **semantic (vector) search** to find the most relevant chunks
- Those chunks are passed to the LLM as **context**, so the answer is grounded in real data — not made up
- **Hybrid mode:** if the question matches the knowledge base (e.g. company-specific), it answers from the docs; if not, the LLM falls back to its own general knowledge

---

## 🛠️ Tech Stack (What I Used)

| Tool / Library | Purpose |
|---|---|
| **FastAPI** | Web framework — to build the API endpoints |
| **Uvicorn** | ASGI server — to run the app |
| **PostgreSQL** | Database — to store chats and messages |
| **SQLAlchemy (async)** | ORM — to handle database tables from Python code |
| **asyncpg** | Async PostgreSQL driver (fast, non-blocking) |
| **Pydantic / pydantic-settings** | Request/response validation and reading `.env` settings |
| **LangChain + Groq** | To call the AI model (Llama 3.3 70B) |
| **ChromaDB** | Local vector database — stores the knowledge base embeddings (no server/extension needed) |
| **sentence-transformers** | Free/local embedding model (`all-MiniLM-L6-v2`) — turns text into numbers (vectors) |
| **python-dotenv** | To load secret keys from the `.env` file |

---

## 🚶 Step by Step — How I Built This Project

### 🔹 Step 1: Environment Setup (First Things First)

First, I created a **virtual environment** so the project's libraries stay isolated from the system:

```bash
# Created the project folder
mkdir fastapi-chatbot
cd fastapi-chatbot

# Created a virtual environment
python -m venv venv

# Activated it (Windows)
venv\Scripts\activate
```

Then I installed the required libraries:

```bash
pip install fastapi uvicorn pydantic pydantic-settings python-dotenv
pip install "sqlalchemy[asyncio]" asyncpg
pip install langchain-groq
```

And saved them into `requirements.txt` so anyone can install everything with a single command.

---

### 🔹 Step 2: R&D (Research — deciding what to use)

Before building, I did some research (R&D) on which tools would work best:

- **Framework:** Django vs Flask vs FastAPI → chose **FastAPI** because it supports async and generates automatic API documentation (Swagger UI).
- **Database:** SQLite vs MySQL vs PostgreSQL → chose **PostgreSQL** because it's production-grade, reliable, and works well with async.
- **AI Model:** OpenAI vs Gemini vs Groq → chose **Groq (Llama 3.3 70B)** because it's extremely **fast** and offers a free tier.
- **How to call the AI:** Direct API vs LangChain → used **LangChain** to make managing chat history (context) easier.

> 💡 Note: The initial plan was to use Gemini (the title in `main.py` still says Gemini), but after R&D I settled on Groq + Llama 3.3.

---

### 🔹 Step 3: Connecting the Database

After the R&D, I connected the **PostgreSQL** database.

**a) Kept secret keys in a `.env` file** (this file is not pushed to git, for security):

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/chatbot_db
GROQ_API_KEY=your_groq_api_key_here
```

**b) `app/config.py`** — Pydantic settings to safely read the `.env` values.

**c) `app/database.py`** — set up the async database engine and session here:
- `create_async_engine` → connection to the database
- `async_sessionmaker` → a separate session for each request
- `get_db()` → a FastAPI dependency that provides a database session to every API

**d) `app/models.py`** — created two database tables:
- **`chat_sessions`** → a record for each chat (id, title, created_at)
- **`chat_messages`** → each message (from user or bot), linked to its session
- Added cascade delete: if a chat is deleted, all its messages are deleted too

> Tables are created automatically — when the app starts, the startup event in `main.py` runs `Base.metadata.create_all`.

---

### 🔹 Step 4: Building the API Endpoints

Next, I built the actual chatbot API endpoints. To keep the code clean, I split it into separate files:

- **`app/schemas.py`** → Pydantic models (to validate input and format output)
- **`app/services/ai_service.py`** → AI logic — sending chat history to Groq/Llama in the right format and getting a reply
- **`app/routers/chat.py`** → all the chat endpoints

**API Endpoints Built:**

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/chat/send` | Send a message → AI replies and both are saved (if no `chat_id` is given, a new chat is created automatically) |
| `GET` | `/api/chat/list` | List of all chats |
| `GET` | `/api/chat/{chat_id}/messages` | Full history of one chat (with pagination) |
| `DELETE` | `/api/chat/{chat_id}` | Delete a chat and all its messages |
| `POST` | `/api/knowledge/ingest` | Load the `data/*.txt` files into the vector database (RAG) |
| `GET` | `/api/knowledge/search` | Test which knowledge chunks match a query (RAG) |

**How the AI service works:** when a user sends a message, the backend fetches that chat's previous history (last 10 messages) and passes it to Llama 3.3, so the AI has context and gives a relevant reply.

---

### 🔹 Step 5: Testing in the Browser (Swagger UI)

After building everything, I ran the app:

```bash
uvicorn app.main:app --reload
```

Then opened it in the browser:

- **API check:** http://127.0.0.1:8000/ → `{"message": "Chatbot server is up and running..."}`
- **Swagger UI (testing):** http://127.0.0.1:8000/docs

On **Swagger UI**, I manually tested every endpoint:
1. `POST /api/chat/send` → sent a message → got the AI's reply ✅
2. `GET /api/chat/list` → the new chat appeared in the list ✅
3. `GET /api/chat/{chat_id}/messages` → got the full conversation history ✅
4. `DELETE /api/chat/{chat_id}` → the chat was deleted ✅

> The benefit of Swagger UI is that you can test all the APIs directly in the browser — no frontend or Postman needed.

---

### 🔹 Step 6: Adding RAG (Knowledge Base) — the Real Learning

After the basic chatbot worked, I added a **RAG layer** so the bot could answer from a custom knowledge base instead of guessing.

**a) Dummy data** — I put some realistic company docs in a `data/` folder (`products.txt`, `refund_policy.txt`, `support_faq.txt`, `shipping_warranty.txt`) for a fictional brand "TechNova".

**b) `app/services/rag_service.py`** — the brain of RAG:
- **Chunking** → breaks big text into smaller pieces (with slight overlap so meaning isn't cut)
- **Embeddings** → `sentence-transformers` converts each chunk into a vector (numbers)
- **Storage** → chunks + vectors are saved in **ChromaDB** (a local folder, `chroma_db/`)
- **Search** → a user query is embedded too, then ChromaDB finds the closest chunks using **cosine distance**

**c) `app/routers/knowledge.py`** — two endpoints to manage the knowledge base:
- `POST /api/knowledge/ingest` → reads all `data/*.txt`, chunks them, and loads them into ChromaDB
- `GET /api/knowledge/search?q=...` → a test endpoint to see which chunks match a query (and their scores)

**d) Hybrid mode** — in `ai_service.py`, if the search finds relevant chunks (distance below a threshold), they're passed to Llama as context. If nothing relevant is found, the LLM just answers from its own general knowledge. So the bot is useful for **both** company-specific and generic questions.

> 💡 Note on the journey: I first tried **pgvector** (a PostgreSQL extension) but the extension wasn't available on my Windows PostgreSQL setup. So I switched to **ChromaDB** — a local, file-based vector database that needs no server extension. Chats still live in PostgreSQL; only the knowledge vectors go to ChromaDB.

**RAG request flow (`POST /api/chat/send`):**

```
User message
   ↓
Vector search in ChromaDB  →  relevant chunks found?
   ↓                              ↓ yes            ↓ no
Save user message         pass chunks         no context
   ↓                      as context              ↓
        →  Llama 3.3 generates the answer  ←
   ↓
Save bot reply  →  return response
```

---

## 📁 Project Structure

```
fastapi-chatbot/
├── app/
│   ├── main.py              # App entry point + startup event
│   ├── config.py            # .env settings (keys, DB URL)
│   ├── database.py          # Async DB engine + session
│   ├── models.py            # Database tables (ChatSession, ChatMessage)
│   ├── schemas.py           # Request/response validation (Pydantic)
│   ├── routers/
│   │   ├── chat.py          # All chat API endpoints
│   │   └── knowledge.py     # RAG endpoints (ingest + search)
│   └── services/
│       ├── ai_service.py    # Groq / Llama 3.3 AI logic (hybrid mode)
│       └── rag_service.py   # RAG brain: chunking, embeddings, vector search
├── data/                    # Knowledge base docs (.txt files for RAG)
├── chroma_db/               # Local vector database (auto-created, not pushed to git)
├── .env                     # Secret keys (not pushed to git)
├── .gitignore
├── requirements.txt         # All dependencies
└── README.md
```

---

## ▶️ How to Run This Project (Setup Guide)

```bash
# 1. Clone / download the project
cd fastapi-chatbot

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file and add your keys
#    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/chatbot_db
#    GROQ_API_KEY=your_key_here

# 5. Run the app
uvicorn app.main:app --reload

# 6. Load the knowledge base into the vector DB (RAG)
#    In Swagger UI, call:  POST /api/knowledge/ingest
#    (or) curl -X POST http://127.0.0.1:8000/api/knowledge/ingest

# 7. Test it in the browser
#    http://127.0.0.1:8000/docs
```

> ⚠️ First run downloads the embedding model (`all-MiniLM-L6-v2`, ~90 MB) — this happens once and may take a minute.

---

## 🔑 Important Notes

- A **Groq API key** is free: https://console.groq.com
- **PostgreSQL** must be installed and running on your system, with a database created (e.g. `chatbot_db`)
- Tables are created automatically — the app builds them on first startup
- **Embeddings are free & local** — `sentence-transformers` runs on your machine, no API key needed for RAG
- Run `POST /api/knowledge/ingest` **once** (or after changing the `data/` files) to load the knowledge base
- Never push the `.env` file to git/GitHub (that's why it's in `.gitignore`)

---

## 📝 Summary (In One Line)

> First did the **environment setup** → then chose tools through **R&D** (FastAPI + PostgreSQL + Groq) → then **connected the database** → then **built the chatbot APIs** → then added a **RAG knowledge base** (embeddings + ChromaDB vector search, with hybrid mode) → and finally **tested everything in the browser (Swagger UI)**. ✅
