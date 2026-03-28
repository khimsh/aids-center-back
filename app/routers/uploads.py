from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.deps import require_editor

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BASE_DIR / "uploads"

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    _: object = Depends(require_editor),
):
    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only image files are allowed")

    content = await file.read()
    await file.close()

    if not content:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")

    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image exceeds 10MB limit")

    UPLOADS_DIR.mkdir(exist_ok=True)
    ext = ALLOWED_IMAGE_CONTENT_TYPES[file.content_type]
    filename = f"{uuid4().hex}{ext}"
    path = UPLOADS_DIR / filename
    path.write_bytes(content)

    return {"url": f"/uploads/{filename}"}
