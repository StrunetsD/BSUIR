import re
import uuid

from qdrant_client.models import PointStruct

from ..config import get_settings
from ..repositories.rag_repository import RagRepository
from ..services.llm_service import LlmService
from ..vector_store import ensure_collection, get_qdrant_client
from .stages import ChunkingStage, EmbeddingStage, PromptStage
from .types import SourceDocument


class RagPipeline:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.repo = RagRepository()
        self.llm = LlmService()
        self.chunking = ChunkingStage()
        self.embedding = EmbeddingStage(self.llm)

    @staticmethod
    def _extract_quoted_title(text: str) -> str | None:
        patterns = (
            r"[«\"“]([^»\"”]{2,120})[»\"”]",
            r"[\"“]([^\"”]{2,120})[\"”]",
        )
        for pattern in patterns:
            match = re.search(pattern, text or "", re.DOTALL)
            if match:
                t = match.group(1).strip()
                if t:
                    return t
        return None

    def _title_match_candidates(self, title: str) -> tuple[str, ...]:
        """Варианты строки заголовка для LIKE (тире, пробелы)."""
        t = (title or "").strip()
        if not t:
            return ()
        seen: set[str] = set()
        out: list[str] = []
        for v in (
            t,
            re.sub(r"\s+", " ", t),
            t.replace("—", "-").replace("–", "-"),
            t.replace("-", "—"),
            re.sub(r"\s*\(\s*фрагмент\s*\)\s*$", "", t, flags=re.IGNORECASE).strip(),
        ):
            if v and v not in seen:
                seen.add(v)
                out.append(v)
        return tuple(out)

    def _contexts_for_pinned_title(self, question: str, top_k: int) -> list[dict] | None:
        title = self._extract_quoted_title(question)
        if not title:
            return None
        cands = self._title_match_candidates(title)
        doc = self.repo.find_document_by_title_candidates(
            *cands,
            self.repo._normalize_title_query(title),
        )
        if not doc:
            return None
        rows = self.repo.list_chunks_for_document(int(doc["id"]), limit=max(top_k, 8))
        if not rows:
            return None
        for i, row in enumerate(rows):
            row["score"] = 1.0 - (i * 0.0005)
        return rows

    def ingest_document(self, document: SourceDocument) -> dict:
        chunks = self.chunking.run(document)
        if not chunks:
            raise ValueError("text is empty after normalization")

        embedded_chunks = self.embedding.run(chunks)
        ensure_collection(len(embedded_chunks[0].vector))

        doc_row = self.repo.create_document(
            title=document.title,
            source=document.source,
            author=document.author,
            raw_text=document.text,
        )
        document_id = int(doc_row["id"])

        points: list[PointStruct] = []
        for item in embedded_chunks:
            point_id = str(uuid.uuid4())
            self.repo.create_chunk(document_id, item.chunk_index, item.text, point_id)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=item.vector,
                    payload={"document_id": document_id, "chunk_index": item.chunk_index},
                )
            )

        get_qdrant_client().upsert(collection_name=self.settings.qdrant_collection, points=points)
        return {
            "ok": True,
            "document": doc_row,
            "chunks_indexed": len(embedded_chunks),
            "collection": self.settings.qdrant_collection,
        }

    def query(self, question: str, top_k: int) -> dict:
        contexts = self.retrieve_contexts(question=question, top_k=top_k)
        if not contexts:
            return {"answer": "Пока нет данных в базе знаний. Сначала загрузите документы.", "contexts": [], "top_k": top_k}
        answer = self.answer_with_context(question=question, contexts=contexts)
        return {"answer": answer, "contexts": contexts, "top_k": top_k}

    def retrieve_contexts(self, question: str, top_k: int) -> list[dict]:
        pinned = self._contexts_for_pinned_title(question, top_k)
        if pinned is not None:
            return pinned[:top_k]

        client = get_qdrant_client()
        collections = {c.name for c in client.get_collections().collections}
        if self.settings.qdrant_collection not in collections:
            return []

        query_vector = self.llm.embed(question)
        hits = client.search(
            collection_name=self.settings.qdrant_collection,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )

        if not hits:
            return []

        contexts: list[dict] = []
        for hit in hits:
            payload = hit.payload or {}
            row = self.repo.get_chunk_with_doc(
                document_id=int(payload.get("document_id")),
                chunk_index=int(payload.get("chunk_index")),
            )
            if row:
                row["score"] = float(hit.score)
                contexts.append(row)
        return contexts

    def answer_with_context(self, question: str, contexts: list[dict]) -> str:
        prompt = PromptStage.run(question=question, contexts=contexts)
        return self.llm.chat(prompt)
