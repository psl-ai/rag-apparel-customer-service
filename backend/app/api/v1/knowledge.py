from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.rbac import require_roles
from app.db.session import get_sync_db_session
from app.schemas.common import ApiResponse
from app.models.knowledge import KnowledgeDocument, KnowledgeDocumentVersion
from app.rag.storage import get_object_storage
from app.services.knowledge import KnowledgeService, KnowledgeVersionService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
admin_access = Depends(require_roles("operator", "admin", "super_admin"))


@router.post("/documents", dependencies=[admin_access])
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form(...),
    product_id: UUID | None = Form(default=None),
    session: Session = Depends(get_sync_db_session),
) -> ApiResponse[dict[str, object]]:
    filename = file.filename or "document.txt"
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    if suffix not in {"md", "markdown", "txt", "csv"}:
        raise AppError("KNOWLEDGE_FILE_TYPE", "仅支持 Markdown、TXT、CSV 文件", 415)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise AppError("KNOWLEDGE_FILE_TOO_LARGE", "文件大小不能超过 5MB", 413)
    document = KnowledgeService(session).ingest(title=title, document_type=document_type, filename=filename, content=content, product_id=product_id)
    return ApiResponse.ok(request_id=request.state.request_id, data={"id": document.id, "version": document.version, "status": document.status})


@router.post("/reindex/{document_id}", dependencies=[admin_access])
def reindex(document_id: UUID, request: Request, session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, int]]:
    document = session.get(KnowledgeDocument, document_id)
    if document is None:
        raise AppError("KNOWLEDGE_NOT_FOUND", "知识文档不存在", 404)
    active = session.scalar(select(KnowledgeDocumentVersion).where(KnowledgeDocumentVersion.document_id == document_id, KnowledgeDocumentVersion.version == document.active_version))
    if active is None:
        raise AppError("KNOWLEDGE_VERSION_NOT_FOUND", "没有可重建索引的版本", 409)
    source = get_object_storage().get(active.object_key)
    if source is None:
        raise AppError("KNOWLEDGE_SOURCE_NOT_FOUND", "源文件不存在", 404)
    version = KnowledgeVersionService(session, get_object_storage()).create_version(source_key=document.source_key or str(document.id), title=document.title, document_type=document.document_type, content=source, product_id=document.product_id)
    from app.rag.indexer import KnowledgeIndexer
    count = KnowledgeIndexer(session, get_object_storage()).index_version(version.id)
    return ApiResponse.ok(request_id=request.state.request_id, data={"chunks": count, "version": version.version})


@router.get("/documents", dependencies=[admin_access])
def list_documents(request: Request, session: Session = Depends(get_sync_db_session)) -> ApiResponse[list[dict[str, object]]]:
    documents = session.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())).all()
    return ApiResponse.ok(request_id=request.state.request_id, data=[{"id": item.id, "title": item.title, "document_type": item.document_type, "status": item.status, "active_version": item.active_version} for item in documents])


@router.delete("/documents/{document_id}", dependencies=[admin_access])
def delete_document(document_id: UUID, request: Request, session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, str]]:
    document = session.get(KnowledgeDocument, document_id)
    if document is None:
        raise AppError("KNOWLEDGE_NOT_FOUND", "知识文档不存在", 404)
    versions = session.scalars(select(KnowledgeDocumentVersion).where(KnowledgeDocumentVersion.document_id == document_id)).all()
    for version in versions:
        get_object_storage().delete(version.object_key)
    session.delete(document)
    session.commit()
    return ApiResponse.ok(request_id=request.state.request_id, data={"id": str(document_id), "status": "deleted"})
