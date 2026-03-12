from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.agent_service import run_agent

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []


@router.post("/chat")
async def chat(body: ChatRequest, request: Request):
    """Stream agent reasoning and response as SSE."""
    return StreamingResponse(
        run_agent(
            question=body.question,
            df=request.app.state.df,
            som=request.app.state.som,
            history=body.history,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
