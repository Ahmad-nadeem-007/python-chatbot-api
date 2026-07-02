# 🤖 FastAPI Chatbot API (Groq + Llama 3.3)

An **AI chatbot backend** built with **FastAPI**, using an **async PostgreSQL** database and **Groq (Llama 3.3 70B)** for AI responses. Chat sessions and messages are stored in the database, and the entire API was tested in the browser using Swagger UI.

---

## 📌 What This Project Does

- User sends a message → the backend saves it in the database
- The AI (Llama 3.3) replies using the previous chat history as context
- The bot's reply is also saved in the database
- The user can view a **list** of all their chats
- The user can fetch the full **history of any chat (with pagination)**
- The user can **delete** a chat (all its messages are deleted via cascade)

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
│   │   └── chat.py          # All chat API endpoints
│   └── services/
│       └── ai_service.py    # Groq / Llama 3.3 AI logic
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

# 6. Test it in the browser
#    http://127.0.0.1:8000/docs
```

---

## 🔑 Important Notes

- A **Groq API key** is free: https://console.groq.com
- **PostgreSQL** must be installed and running on your system, with a database created (e.g. `chatbot_db`)
- Tables are created automatically — the app builds them on first startup
- Never push the `.env` file to git/GitHub (that's why it's in `.gitignore`)

---

## 📝 Summary (In One Line)

> First did the **environment setup** → then chose tools through **R&D** (FastAPI + PostgreSQL + Groq) → then **connected the database** → then **built the chatbot APIs** → and finally **tested everything in the browser (Swagger UI)**. ✅
