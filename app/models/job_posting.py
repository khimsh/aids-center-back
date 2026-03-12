from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)

    # Bilingual content
    title_ka       = Column(Text, nullable=False)
    title_en       = Column(Text, nullable=True)
    description_ka = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    department_ka  = Column(Text, nullable=True)
    department_en  = Column(Text, nullable=True)

    # Deadline
    deadline = Column(DateTime(timezone=True), nullable=True)

    # Publishing
    published    = Column(Boolean, server_default="false", nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
