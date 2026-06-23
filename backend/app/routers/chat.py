from fastapi import APIRouter

from app.models import ChatRequest, ChatResponse
from app.services.faq_search import answer_faq

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def create_chat_reply(payload: ChatRequest) -> ChatResponse:
    return answer_faq(payload.message)
