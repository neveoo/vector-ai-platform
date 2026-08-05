"""
The async pipeline that runs after a document is uploaded:
extract text -> chunk -> embed -> store chunks -> classify -> mark ready.

Runs as a Celery task so upload requests return immediately and large
documents don't block the API.
"""
from uuid import UUID

from app.core.celery_app import celery_app
from app.db.session import SessionLocal, set_tenant_context
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.services.audit import record_audit_event
from app.services.classification import classify_document
from app.services.embeddings import embed_texts
from app.services.storage import download_file_from_storage
from app.services.text_extraction import chunk_text, extract_text


@celery_app.task(name="process_document", bind=True, max_retries=3)
def process_document_task(self, document_id: str, tenant_id: str) -> None:
    db = SessionLocal()
    try:
        set_tenant_context(db, UUID(tenant_id))
        document = db.get(Document, UUID(document_id))
        if document is None:
            return  # deleted before processing started; nothing to do

        document.status = DocumentStatus.PROCESSING
        db.commit()

        try:
            raw_bytes = download_file_from_storage(document.storage_key)
            full_text = extract_text(raw_bytes, document.mime_type)
            chunks = chunk_text(full_text)

            embeddings = embed_texts([c.content for c in chunks])
            for chunk, vector in zip(chunks, embeddings):
                db.add(
                    DocumentChunk(
                        tenant_id=document.tenant_id,
                        document_id=document.id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        page_number=chunk.page_number,
                        section_heading=chunk.section_heading,
                        embedding=vector,
                    )
                )

            predicted_class, confidence, method = classify_document(full_text[:8000])
            document.predicted_class = predicted_class
            document.predicted_class_confidence = confidence
            document.classification_method = method
            document.status = DocumentStatus.READY

            record_audit_event(
                db,
                tenant_id=document.tenant_id,
                actor_user_id=None,  # system action
                action="document.processed",
                resource_type="document",
                resource_id=document.id,
                details={"chunk_count": len(chunks), "predicted_class": predicted_class, "method": method},
            )
            db.commit()

        except Exception as exc:  # noqa: BLE001 -- deliberately broad: any failure marks the doc FAILED
            document.status = DocumentStatus.FAILED
            record_audit_event(
                db,
                tenant_id=document.tenant_id,
                actor_user_id=None,
                action="document.processing_failed",
                resource_type="document",
                resource_id=document.id,
                details={"error": str(exc)},
            )
            db.commit()
            raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
