from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import ChatSession, ChatMessage
from app.schemas import MessageSend, PaginatedMessages, ChatSessionResponse, MessageResponse
from app.services.ai_service import ai_service

router = APIRouter(prefix="/chat", tags=["Chat"])


# 1. SEND MESSAGE — auto-creates session if chat_id not provided
@router.post("/send", response_model=MessageResponse)
async def send_message(payload: MessageSend, db: AsyncSession = Depends(get_db)):
    try:
        chat_id = payload.chat_id

        if not chat_id:
            new_session = ChatSession(title=payload.message[:50])
            db.add(new_session)
            await db.flush()
            chat_id = new_session.id
        else:
            result = await db.execute(select(ChatSession).where(ChatSession.id == chat_id))
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Chat session not found")

        user_msg = ChatMessage(session_id=chat_id, sender="user", content=payload.message)
        db.add(user_msg)
        await db.flush()

        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(10)
        )
        history = history_result.scalars().all()

        bot_content = await ai_service.get_bot_response(payload.message, history)

        bot_msg = ChatMessage(session_id=chat_id, sender="bot", content=bot_content)
        db.add(bot_msg)
        await db.commit()
        await db.refresh(bot_msg)

        return bot_msg

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# 2. GET ALL CHATS LIST — /list must be before /{chat_id} routes
@router.get("/list", response_model=list[ChatSessionResponse])
async def get_all_chats(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ChatSession).order_by(ChatSession.created_at.desc()))
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# 3. GET CHAT MESSAGES WITH PAGINATION
@router.get("/{chat_id}/messages", response_model=PaginatedMessages)
async def get_chat_history(
    chat_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    try:
        session_result = await db.execute(select(ChatSession).where(ChatSession.id == chat_id))
        if not session_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Chat session not found")

        count_result = await db.execute(
            select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == chat_id)
        )
        total_messages = count_result.scalar() or 0

        offset = (page - 1) * limit

        msg_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_id)
            .order_by(ChatMessage.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        messages = msg_result.scalars().all()
        messages.reverse()

        return {
            "chat_id": chat_id,
            "total_messages": total_messages,
            "page": page,
            "limit": limit,
            "messages": messages,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# 4. DELETE CHAT SESSION (cascades to all messages)
@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ChatSession).where(ChatSession.id == chat_id))
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        await db.delete(session)
        await db.commit()
        return {"status": "success", "message": f"Chat {chat_id} deleted successfully."}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
