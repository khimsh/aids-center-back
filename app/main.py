from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.articles import router as articles_router
from app.routers.doctors import router as doctors_router
from app.routers.job_postings import router as job_postings_router

app = FastAPI(
    title="AIDS Center API",
    description="Backend API for aidscenter.ge",
    version="0.1.0",
)

# CORS — allow Astro dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",  # Astro dev
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(articles_router)
app.include_router(doctors_router)
app.include_router(job_postings_router)


@app.get("/health")
async def health():
    return {"status": "ok"}