from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from ..schemas import RagIngestRequest, RagIngestUrlsRequest, RagQueryRequest
from ..services.internet_ingest_service import InternetIngestService, UrlIngestItem
from ..services.rag_service import RagService

rag_bp = Blueprint("rag", __name__)
rag_service = RagService()
internet_ingest_service = InternetIngestService()


@rag_bp.post("/api/rag/ingest")
def rag_ingest():
    try:
        payload = RagIngestRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": exc.errors()}), 400

    try:
        return jsonify(
            rag_service.ingest(
                title=payload.title.strip(),
                source=payload.source,
                author=payload.author.strip() if payload.author else None,
                text=payload.text.strip(),
            )
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Failed to ingest: {exc}"}), 500


@rag_bp.post("/api/rag/query")
def rag_query():
    try:
        payload = RagQueryRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": exc.errors()}), 400

    try:
        return jsonify(rag_service.query(question=payload.question.strip(), top_k=payload.top_k))
    except Exception as exc:
        return jsonify({"error": f"RAG query failed: {exc}"}), 500


@rag_bp.post("/api/rag/upload")
def rag_upload():
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400

    file_obj = request.files["file"]
    if not file_obj.filename:
        return jsonify({"error": "filename is empty"}), 400

    content = file_obj.read()
    if not content:
        return jsonify({"error": "uploaded file is empty"}), 400

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("cp1251", errors="ignore")

    title = (request.form.get("title") or file_obj.filename).strip()
    author = (request.form.get("author") or "").strip() or None
    source = (request.form.get("source") or "upload").strip() or "upload"

    try:
        return jsonify(
            rag_service.ingest(
                title=title,
                source=source,
                author=author,
                text=text,
            )
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Failed to upload document: {exc}"}), 500


@rag_bp.get("/api/rag/documents")
def rag_documents():
    limit_raw = request.args.get("limit", "100")
    try:
        limit = max(1, min(500, int(limit_raw)))
    except ValueError:
        limit = 100
    return jsonify(rag_service.list_documents(limit=limit))


@rag_bp.post("/api/rag/ingest-urls")
def rag_ingest_urls():
    try:
        payload = RagIngestUrlsRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": exc.errors()}), 400

    items = [
        UrlIngestItem(
            url=item.url.strip(),
            title=item.title.strip() if item.title else None,
            author=item.author.strip() if item.author else None,
            source=item.source.strip() if item.source else None,
        )
        for item in payload.items
    ]

    try:
        return jsonify(
            internet_ingest_service.ingest_urls(
                items=items,
                max_chars_per_doc=payload.max_chars_per_doc,
            )
        )
    except Exception as exc:
        return jsonify({"error": f"Failed to ingest URLs: {exc}"}), 500
