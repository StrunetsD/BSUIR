from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from ..config import get_settings
from ..repositories.chat_repository import ChatRepository
from ..schemas import ChatRequest, EditMessageRequest, TruncateMessagesRequest
from ..services.rag_service import RagService

chat_bp = Blueprint("chat", __name__)
chat_repo = ChatRepository()
rag_service = RagService()
settings = get_settings()


@chat_bp.get("/api/messages")
def list_messages():
    limit_raw = request.args.get("limit", "100")
    try:
        limit = max(1, min(500, int(limit_raw)))
    except ValueError:
        limit = 100
    return jsonify(chat_repo.list_messages(limit=limit))


@chat_bp.post("/api/chat")
def chat():
    try:
        payload = ChatRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": exc.errors()}), 400

    user_text = payload.message.strip()
    if not user_text:
        return jsonify({"error": "message is required"}), 400

    recent_history_desc = chat_repo.get_recent_history(limit=settings.chat_history_limit)
    history_for_llm = list(reversed(recent_history_desc))
    rag_result = rag_service.ask_with_history(
        question=user_text,
        history=history_for_llm,
        top_k=settings.chat_top_k,
    )
    bot_text = rag_result["answer"]
    return jsonify(chat_repo.save_pair(user_text=user_text, bot_text=bot_text))


@chat_bp.post("/api/messages/clear")
def clear_messages():
    chat_repo.clear()
    return jsonify({"ok": True})


@chat_bp.post("/api/messages/truncate")
def truncate_messages():
    try:
        payload = TruncateMessagesRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": exc.errors()}), 400
    chat_repo.truncate(payload.keep)
    return jsonify({"ok": True, "keep": payload.keep})


@chat_bp.post("/api/messages/<int:message_id>")
def edit_message(message_id: int):
    try:
        payload = EditMessageRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": exc.errors()}), 400

    row = chat_repo.edit(message_id=message_id, user_text=payload.user_text.strip(), bot_text=payload.bot_text.strip())
    if row is None:
        return jsonify({"error": "Message not found"}), 404
    return jsonify(row)
