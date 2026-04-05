from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin, require_editor
from app.database import get_db
from app.models.doctor import Doctor, DoctorTranslation
from app.schemas.doctor import (
    DoctorCreate,
    DoctorMoveRequest,
    DoctorOut,
    DoctorTranslationCreate,
    DoctorTranslationOut,
    DoctorTranslationUpdate,
    DoctorReorderByIdsRequest,
    DoctorReorderRequest,
    DoctorUpdate,
)


router = APIRouter(prefix="/api/doctors", tags=["doctors"])


def _normalize_lang(lang: str) -> str:
    return lang.strip().lower()


@router.get("", response_model=list[DoctorOut])
async def list_doctors(
    search: Optional[str] = Query(None, description="Free-text search across name/specialty/department"),
    q: Optional[str] = Query(None, description="Alias for search"),
    query: Optional[str] = Query(None, description="Alias for search"),
    name: Optional[str] = Query(None, description="Filter by doctor name"),
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    specialization: Optional[str] = Query(None, description="Alias for specialty"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Doctor)

    effective_search = (search or q or query)
    if effective_search:
        term = f"%{effective_search.strip()}%"
        stmt = stmt.where(
            or_(
                Doctor.name.ilike(term),
                Doctor.specialty.ilike(term),
                Doctor.department.ilike(term),
            )
        )

    if name:
        stmt = stmt.where(Doctor.name.ilike(f"%{name.strip()}%"))

    effective_specialty = specialty or specialization
    if effective_specialty:
        stmt = stmt.where(Doctor.specialty.ilike(f"%{effective_specialty.strip()}%"))
    if department:
        stmt = stmt.where(Doctor.department.ilike(f"%{department.strip()}%"))

    result = await db.execute(
        stmt.order_by(Doctor.sort_order.asc(), Doctor.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{doctor_id}", response_model=DoctorOut)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.post("", response_model=DoctorOut, status_code=201)
async def create_doctor(
    payload: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_editor),
):
    payload_data = payload.model_dump()
    if payload_data.get("sort_order") is None:
        max_sort_result = await db.execute(select(func.max(Doctor.sort_order)))
        max_sort = max_sort_result.scalar_one_or_none() or 0
        payload_data["sort_order"] = max_sort + 1

    doctor = Doctor(**payload_data)
    db.add(doctor)
    await db.flush()
    await db.refresh(doctor)
    return doctor


@router.put("/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: int,
    payload: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_editor),
):
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(doctor, field, value)

    await db.flush()
    await db.refresh(doctor)
    return doctor


@router.patch("/reorder", response_model=list[DoctorOut])
async def reorder_doctors(
    payload: DoctorReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_editor),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="items cannot be empty")

    ids = [item.id for item in payload.items]
    sort_orders = [item.sort_order for item in payload.items]

    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=400, detail="duplicate doctor ids are not allowed")
    if len(sort_orders) != len(set(sort_orders)):
        raise HTTPException(status_code=400, detail="duplicate sort_order values are not allowed")
    if any(sort_order < 0 for sort_order in sort_orders):
        raise HTTPException(status_code=400, detail="sort_order must be >= 0")

    existing_result = await db.execute(select(Doctor).where(Doctor.id.in_(ids)))
    existing_doctors = {doctor.id: doctor for doctor in existing_result.scalars().all()}

    missing_ids = [doctor_id for doctor_id in ids if doctor_id not in existing_doctors]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Doctors not found: {missing_ids}")

    for item in payload.items:
        existing_doctors[item.id].sort_order = item.sort_order

    await db.flush()

    ordered_result = await db.execute(
        select(Doctor).order_by(Doctor.sort_order.asc(), Doctor.created_at.desc())
    )
    return ordered_result.scalars().all()


@router.patch("/reorder-by-ids", response_model=list[DoctorOut])
async def reorder_doctors_by_ids(
    payload: DoctorReorderByIdsRequest,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_editor),
):
    if not payload.ids:
        raise HTTPException(status_code=400, detail="ids cannot be empty")
    if len(payload.ids) != len(set(payload.ids)):
        raise HTTPException(status_code=400, detail="duplicate doctor ids are not allowed")

    existing_result = await db.execute(select(Doctor).where(Doctor.id.in_(payload.ids)))
    existing_doctors = {doctor.id: doctor for doctor in existing_result.scalars().all()}

    missing_ids = [doctor_id for doctor_id in payload.ids if doctor_id not in existing_doctors]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Doctors not found: {missing_ids}")

    for index, doctor_id in enumerate(payload.ids, start=1):
        existing_doctors[doctor_id].sort_order = index

    await db.flush()

    ordered_result = await db.execute(
        select(Doctor).order_by(Doctor.sort_order.asc(), Doctor.created_at.desc())
    )
    return ordered_result.scalars().all()


@router.patch("/reorder-move", response_model=list[DoctorOut])
async def move_doctors(
    payload: DoctorMoveRequest,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_editor),
):
    if not payload.ids:
        raise HTTPException(status_code=400, detail="ids cannot be empty")
    if len(payload.ids) != len(set(payload.ids)):
        raise HTTPException(status_code=400, detail="duplicate doctor ids are not allowed")

    has_before = payload.before_id is not None
    has_after = payload.after_id is not None
    if has_before == has_after:
        raise HTTPException(
            status_code=400,
            detail="Exactly one of before_id or after_id must be provided",
        )

    ordered_result = await db.execute(
        select(Doctor).order_by(Doctor.sort_order.asc(), Doctor.created_at.desc())
    )
    ordered_doctors = ordered_result.scalars().all()

    doctors_by_id = {doctor.id: doctor for doctor in ordered_doctors}

    missing_ids = [doctor_id for doctor_id in payload.ids if doctor_id not in doctors_by_id]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Doctors not found: {missing_ids}")

    anchor_id = payload.before_id if has_before else payload.after_id
    if anchor_id not in doctors_by_id:
        raise HTTPException(status_code=404, detail=f"Doctor not found: {anchor_id}")
    if anchor_id in payload.ids:
        raise HTTPException(status_code=400, detail="anchor id cannot be one of moved ids")

    move_ids = payload.ids
    remaining_ids = [doctor.id for doctor in ordered_doctors if doctor.id not in move_ids]

    anchor_index = remaining_ids.index(anchor_id)
    insert_index = anchor_index if has_before else anchor_index + 1
    new_order_ids = remaining_ids[:insert_index] + move_ids + remaining_ids[insert_index:]

    for sort_order, doctor_id in enumerate(new_order_ids, start=1):
        doctors_by_id[doctor_id].sort_order = sort_order

    await db.flush()

    final_result = await db.execute(
        select(Doctor).order_by(Doctor.sort_order.asc(), Doctor.created_at.desc())
    )
    return final_result.scalars().all()


@router.delete("/{doctor_id}", status_code=204)
async def delete_doctor(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_admin),
):
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    await db.delete(doctor)


@router.get("/{doctor_id}/translations", response_model=list[DoctorTranslationOut])
async def list_doctor_translations(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
):
    doctor_result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = doctor_result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    result = await db.execute(
        select(DoctorTranslation)
        .where(DoctorTranslation.doctor_id == doctor_id)
        .order_by(DoctorTranslation.lang.asc())
    )
    return result.scalars().all()


@router.get("/{doctor_id}/translations/{lang}", response_model=DoctorTranslationOut)
async def get_doctor_translation(
    doctor_id: int,
    lang: str,
    db: AsyncSession = Depends(get_db),
):
    normalized_lang = _normalize_lang(lang)
    result = await db.execute(
        select(DoctorTranslation).where(
            DoctorTranslation.doctor_id == doctor_id,
            DoctorTranslation.lang == normalized_lang,
        )
    )
    translation = result.scalar_one_or_none()
    if not translation:
        raise HTTPException(status_code=404, detail="Doctor translation not found")
    return translation


@router.post("/{doctor_id}/translations", response_model=DoctorTranslationOut, status_code=201)
async def create_doctor_translation(
    doctor_id: int,
    payload: DoctorTranslationCreate,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_editor),
):
    doctor_result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = doctor_result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    normalized_lang = _normalize_lang(payload.lang)
    existing_result = await db.execute(
        select(DoctorTranslation).where(
            DoctorTranslation.doctor_id == doctor_id,
            DoctorTranslation.lang == normalized_lang,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Translation for this language already exists")

    translation = DoctorTranslation(
        doctor_id=doctor_id,
        lang=normalized_lang,
        name=payload.name,
        specialty=payload.specialty,
        degree=payload.degree,
        department=payload.department,
        education=payload.education,
        experience=payload.experience,
        pedagogical_experience=payload.pedagogical_experience,
        memberships=payload.memberships,
        publications=payload.publications,
        expertise=payload.expertise,
    )
    db.add(translation)
    await db.flush()
    await db.refresh(translation)
    return translation


@router.put("/{doctor_id}/translations/{lang}", response_model=DoctorTranslationOut)
async def update_doctor_translation(
    doctor_id: int,
    lang: str,
    payload: DoctorTranslationUpdate,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_editor),
):
    normalized_lang = _normalize_lang(lang)
    result = await db.execute(
        select(DoctorTranslation).where(
            DoctorTranslation.doctor_id == doctor_id,
            DoctorTranslation.lang == normalized_lang,
        )
    )
    translation = result.scalar_one_or_none()
    if not translation:
        raise HTTPException(status_code=404, detail="Doctor translation not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(translation, field, value)

    await db.flush()
    await db.refresh(translation)
    return translation
