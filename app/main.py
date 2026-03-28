from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.routers.articles import router as articles_router
from app.routers.auth import router as auth_router
from app.routers.doctors import router as doctors_router
from app.routers.job_postings import router as job_postings_router
from app.routers.uploads import router as uploads_router
from app.routers.users import router as users_router

app = FastAPI(
    title="AIDS Center API",
    description="Backend API for aidscenter.ge",
    version="0.1.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# CORS — allow Astro dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",  # Astro dev
        "http://localhost:3000",
        "http://localhost:5173",  # Vite / React admin dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(articles_router)
app.include_router(doctors_router)
app.include_router(job_postings_router)
app.include_router(users_router)
app.include_router(uploads_router)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}