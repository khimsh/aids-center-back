from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin, require_editor
from app.database import get_db
from app.models.job_posting import JobPosting
from app.schemas.job_posting import JobPostingCreate, JobPostingOut, JobPostingUpdate


router = APIRouter(prefix="/api/job-postings", tags=["job-postings"])


# ── PUBLIC ENDPOINTS ────────────────────────────────────────────────────────

@router.get("", response_model=list[JobPostingOut])
async def list_job_postings(db: AsyncSession = Depends(get_db)):
    """All published job postings, newest first."""
    result = await db.execute(
        select(JobPosting)
        .where(JobPosting.published == True)
        .order_by(JobPosting.published_at.desc().nullslast(), JobPosting.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobPostingOut)
async def get_job_posting(job_id: int, db: AsyncSession = Depends(get_db)):
    """Single published job posting."""
    result = await db.execute(
        select(JobPosting).where(JobPosting.id == job_id, JobPosting.published == True)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    return job


# ── ADMIN ENDPOINTS ────────────────────────────────────────────────────────

@router.post("", response_model=JobPostingOut, status_code=201)
async def create_job_posting(
    payload: JobPostingCreate,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_editor),
):
    data = payload.model_dump(exclude={"published_at"})

    published_at = None
    if payload.published:
        published_at = payload.published_at or datetime.now(timezone.utc)

    job = JobPosting(**data, published_at=published_at)
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


@router.put("/{job_id}", response_model=JobPostingOut)
async def update_job_posting(
    job_id: int,
    payload: JobPostingUpdate,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_editor),
):
    result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")

    updates = payload.model_dump(exclude_unset=True)

    # Auto-set published_at when publishing for the first time
    if updates.get("published") and not job.published:
        updates.setdefault("published_at", datetime.now(timezone.utc))

    for field, value in updates.items():
        setattr(job, field, value)

    await db.flush()
    await db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=204)
async def delete_job_posting(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    _: AsyncSession = Depends(require_admin),
):
    result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    await db.delete(job)
