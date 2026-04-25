from fastapi import APIRouter

from app.core.chat_client import run_chat
from app.core.schema import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def chat_message(req: ChatRequest) -> ChatResponse:
    return await run_chat(req)
