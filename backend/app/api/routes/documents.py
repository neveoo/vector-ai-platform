"""
Document upload + listing routes.

This is the reference implementation of the pattern every route in
this app follows: depend on get_tenant_db (RLS context is already set
for us), do the work, write an audit event, return a pydantic schema.
Processing (chunking + embedding + classification) happens
asynchronously via a Celery task -- see app/services/document_processing.py.
"""
import uuid

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_tenant_db, get_current_user, CurrentUser
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentRead, DocumentUploadResponse
from app.services.audit import record_audit_event
from app.services.storage import upload_file_to_storage

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_tenant_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentUploadResponse:
    contents = await file.read()
    storage_key = upload_file_to_storage(
        tenant_id=current_user.tenant_id, filename=file.filename, contents=contents
    )

    document = Document(
        tenant_id=current_user.tenant_id,
        uploaded_by=current_user.user_id,
        filename=file.filename,
        storage_key=storage_key,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        status=DocumentStatus.UPLOADED,
    )
    db.add(document)
    db.flush()

    record_audit_event(
        db,
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.user_id,
        action="document.upload",
        resource_type="document",
        resource_id=document.id,
        details={"filename": file.filename, "size_bytes": len(contents)},
    )
    db.commit()
    db.refresh(document)

    # Kick off async processing (chunk -> embed -> classify). Fire-and-forget
    # from the request's perspective; status transitions are visible via
    # GET /documents/{id} as the Celery task progresses.
    from app.services.document_processing import process_document_task

    process_document_task.delay(str(document.id), str(current_user.tenant_id))

    return DocumentUploadResponse(document=DocumentRead.model_validate(document))


@router.get("", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_tenant_db)) -> list[DocumentRead]:
    # No explicit tenant_id filter here -- RLS (see set_tenant_context)
    # guarantees this session only ever sees the current tenant's rows.
    documents = db.execute(select(Document).order_by(Document.created_at.desc())).scalars().all()
    return [DocumentRead.model_validate(d) for d in documents]


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_tenant_db)) -> DocumentRead:
    document = db.get(Document, document_id)
    if document is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentRead.model_validate(document)
