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

    async def get_bot_response(self, user_query: str, chat_history: list) -> str:
        try:
            messages = []
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
