from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorOut, DoctorUpdate


router = APIRouter(prefix="/api/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorOut])
async def list_doctors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).order_by(Doctor.created_at.desc()))
    return result.scalars().all()


@router.get("/{doctor_id}", response_model=DoctorOut)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.post("", response_model=DoctorOut, status_code=201)
async def create_doctor(payload: DoctorCreate, db: AsyncSession = Depends(get_db)):
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    await db.flush()
    await db.refresh(doctor)
    return doctor


@router.put("/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: int,
    payload: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
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


@router.delete("/{doctor_id}", status_code=204)
async def delete_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    await db.delete(doctor)
