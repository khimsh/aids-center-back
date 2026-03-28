from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
import re


# ── Helpers ────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """
    Slug generator that preserves non-ASCII Unicode characters (e.g., Georgian).
    """
    text = text.lower().strip()
    # Keep Unicode word characters, spaces, and hyphens
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    # Collapse multiple spaces/underscores/hyphens into single hyphen
    text = re.sub(r"[\s_-]+", "-", text)
    # Strip leading/trailing hyphens
    text = re.sub(r"^-+|-+$", "", text)
    return text or "article"


# ── Request schemas ─────────────────────────────────────────────────────────

class ArticleCreate(BaseModel):
    title_ka:     str
    title_en:     Optional[str] = None
    body_ka:      Optional[str] = None
    body_en:      Optional[str] = None
    image_url:    Optional[str] = None
    category:     Optional[str] = None
    featured:     bool = False
    published:    bool = False
    published_at: Optional[datetime] = None
    slug:         Optional[str] = None  # auto-generated if not provided

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        allowed = {"news", "program", "equipment", "event", "vacancy", None}
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v


class ArticleUpdate(BaseModel):
    """All fields optional — only send what changed."""
    title_ka:     Optional[str] = None
    title_en:     Optional[str] = None
    body_ka:      Optional[str] = None
    body_en:      Optional[str] = None
    image_url:    Optional[str] = None
    category:     Optional[str] = None
    featured:     Optional[bool] = None
    published:    Optional[bool] = None
    published_at: Optional[datetime] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        allowed = {"news", "program", "equipment", "event", "vacancy", None}
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v


# ── Response schema ─────────────────────────────────────────────────────────

class ArticleOut(BaseModel):
    id:           int
    slug:         str
    title_ka:     str
    title_en:     Optional[str]
    body_ka:      Optional[str]
    body_en:      Optional[str]
    image_url:    Optional[str]
    category:     Optional[str]
    featured:     bool
    published:    bool
    published_at: Optional[datetime]
    created_at:   datetime
    updated_at:   datetime
    created_by:   Optional[int]

    model_config = {"from_attributes": True}


class ArticleListOut(BaseModel):
    """Lighter schema for list views — no body fields."""
    id:           int
    slug:         str
    title_ka:     str
    title_en:     Optional[str]
    image_url:    Optional[str]
    category:     Optional[str]
    featured:     bool
    published:    bool
    published_at: Optional[datetime]
    created_at:   datetime
    created_by:   Optional[int]

    model_config = {"from_attributes": True}


class PaginatedArticles(BaseModel):
    total:    int
    page:     int
    per_page: int
    items:    list[ArticleListOut]