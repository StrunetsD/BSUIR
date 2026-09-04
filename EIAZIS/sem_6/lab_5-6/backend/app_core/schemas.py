from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(default="")


class EditMessageRequest(BaseModel):
    user_text: str
    bot_text: str


class TruncateMessagesRequest(BaseModel):
    keep: int = Field(default=0, ge=0)


class RagIngestRequest(BaseModel):
    title: str
    author: str | None = None
    source: str | None = None
    text: str


class RagQueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=4, ge=1, le=10)


class RagQueryResponse(BaseModel):
    answer: str
    contexts: list[dict[str, Any]]
    top_k: int


class RagIngestUrlItem(BaseModel):
    url: str
    title: str | None = None
    author: str | None = None
    source: str | None = None


class RagIngestUrlsRequest(BaseModel):
    items: list[RagIngestUrlItem] = Field(default_factory=list, min_length=1, max_length=100)
    max_chars_per_doc: int = Field(default=12000, ge=500, le=50000)
