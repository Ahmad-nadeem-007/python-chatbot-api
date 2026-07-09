from langchain_groq import ChatGroq
from fastapi import HTTPException
from app.config import settings


class AIService:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            temperature=0.7,
        )

    async def get_bot_response(self, user_query: str, chat_history: list, context: str = "") -> str:
        try:
            messages = []

            # RAG (Hybrid): if relevant context is found, the AI uses it;
            # if the context is empty (weak match), the AI answers from its own general knowledge
            if context:
                system_prompt = (
                    "You are TechNova's helpful assistant. Use the context below to answer "
                    "the user's question when it is relevant. If the context does not contain "
                    "the answer, answer using your own general knowledge.\n\n"
                    f"Context:\n{context}"
                )
                messages.append(("system", system_prompt))

            for msg in chat_history:
                if msg.sender == "user":
                    messages.append(("human", msg.content))
                else:
                    messages.append(("ai", msg.content))

            messages.append(("human", user_query))

            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")


ai_service = AIService()
