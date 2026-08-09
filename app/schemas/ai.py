"""Chat schemas for Phase 9 (expanded AI)."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.ai_message import MessageRole


class AIChatRequest(BaseModel):
    message: str


class AIChatResponse(BaseModel):
    reply: str


class AIMessageRead(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}