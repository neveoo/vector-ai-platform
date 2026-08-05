from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, rag
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server; add prod frontend origin here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix=settings.api_v1_prefix)
app.include_router(rag.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
