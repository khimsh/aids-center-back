from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    picture = Column(String(500), nullable=True)
    profile_url = Column(String(500), nullable=True)
    specialty = Column(String(255), nullable=True)
    degree = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    education = Column(Text, nullable=False)
    experience = Column(Text, nullable=False)
    pedagogical_experience = Column(Text, nullable=True)
    memberships = Column(Text, nullable=True)
    publications = Column(Text, nullable=True)
    expertise = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DoctorTranslation(Base):
    __tablename__ = "doctor_translations"
    __table_args__ = (
        UniqueConstraint("doctor_id", "lang", name="uq_doctor_translations_doctor_lang"),
    )

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    lang = Column(String(5), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    specialty = Column(String(255), nullable=True)
    degree = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)

    education = Column(Text, nullable=False)
    experience = Column(Text, nullable=False)
    pedagogical_experience = Column(Text, nullable=True)
    memberships = Column(Text, nullable=True)
    publications = Column(Text, nullable=True)
    expertise = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
