from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class KnowledgeDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    slug: str
    category: str
    is_demo: bool


class KnowledgeDocumentDetailOut(KnowledgeDocumentOut):
    content: str


class KnowledgeDocumentCreate(BaseModel):
    title: str
    slug: str
    category: str
    content: str
    is_demo: bool = True


class KnowledgeSourceOut(BaseModel):
    document_title: str
    document_slug: str
    excerpt: str
    relevance: float


class KnowledgeAskRequest(BaseModel):
    query: str
    category: Optional[str] = None


class KnowledgeAskResponse(BaseModel):
    answer: Optional[str] = None
    answered_via: Optional[str] = None  # "ai" | "excerpts" | None
    sources: List[KnowledgeSourceOut] = []
    message: Optional[str] = None  # set when nothing relevant was found
