from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db
from app.services.rag import answer_question, semantic_search

router = APIRouter(tags=["search & rag"])


class SearchRequest(BaseModel):
    query: str
    top_k: int | None = None


class QuestionRequest(BaseModel):
    question: str


@router.post("/search")
def search(request: SearchRequest, db: Session = Depends(get_tenant_db)) -> list[dict]:
    results = semantic_search(db, request.query, request.top_k)
    return [
        {
            "document_id": str(r.document_id),
            "filename": r.filename,
            "content": r.content,
            "similarity": round(r.similarity, 3),
            "page_number": r.page_number,
        }
        for r in results
    ]


@router.post("/ask")
def ask(request: QuestionRequest, db: Session = Depends(get_tenant_db)) -> dict:
    return answer_question(db, request.question)
