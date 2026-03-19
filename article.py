from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id            = Column(Integer, primary_key=True, index=True)
    slug          = Column(String(255), unique=True, nullable=False, index=True)

    # Bilingual content
    title_ka      = Column(Text, nullable=False)
    title_en      = Column(Text, nullable=True)
    body_ka       = Column(Text, nullable=True)   # Quill delta JSON or HTML
    body_en       = Column(Text, nullable=True)

    # Media
    image_url     = Column(String(500), nullable=True)

    # Categorisation
    category      = Column(String(50), nullable=True)
    # values: 'news' | 'program' | 'equipment' | 'event' | 'vacancy'

    # Publishing
    featured      = Column(Boolean, default=False, nullable=False)
    published     = Column(Boolean, default=False, nullable=False)
    published_at  = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())