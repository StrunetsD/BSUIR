import re
from typing import Iterable

from ..config import get_settings
from ..services.llm_service import LlmService
from .types import EmbeddedChunk, SourceDocument, TextChunk

FACTUAL_DISCIPLINE_RU = (
    "Не смешивай разных авторов и их произведения: не приписывай известный текст одному автору, "
    "если он общепризнанно связан с другим.\n"
    "Не выдумывай «настоящие имена», даты и биографические факты. Если контекст их не подтверждает — "
    "скажи, что в базе нет надёжных сведений, и не заполняй пробелы домыслами.\n"
    "Если в контексте нет материалов о лице из вопроса, не утверждай, что такого писателя "
    "«не существует» в литературе; скажи, что в загруженных документах нет информации и при "
    "желании предложи добавить источники."
)


class ChunkingStage:
    def __init__(self) -> None:
        self.settings = get_settings()

    def run(self, document: SourceDocument) -> list[TextChunk]:
        normalized = re.sub(r"\s+", " ", document.text or "").strip()
        if not normalized:
            return []

        chunks: list[TextChunk] = []
        start = 0
        idx = 0
        while start < len(normalized):
            end = min(start + self.settings.rag_chunk_size, len(normalized))
            chunk_text = normalized[start:end].strip()
            if chunk_text:
                chunks.append(TextChunk(chunk_index=idx, text=chunk_text))
                idx += 1
            if end == len(normalized):
                break
            start = max(0, end - self.settings.rag_chunk_overlap)
        return chunks


class EmbeddingStage:
    def __init__(self, llm_service: LlmService) -> None:
        self.llm = llm_service

    def run(self, chunks: Iterable[TextChunk]) -> list[EmbeddedChunk]:
        embedded: list[EmbeddedChunk] = []
        for chunk in chunks:
            vector = self.llm.embed(chunk.text)
            embedded.append(
                EmbeddedChunk(
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    vector=vector,
                )
            )
        return embedded


class PromptStage:
    @staticmethod
    def run(question: str, contexts: list[dict]) -> str:
        context_block = "\n\n".join(
            [
                (
                    f"[Документ: {item['title']}; автор: {item.get('author') or 'не указан'}; "
                    f"chunk={item['chunk_index']}; score={item['score']:.3f}]\n{item['chunk_text']}"
                )
                for item in contexts
            ]
        )
        return (
            "Ты ассистент по литературе. Отвечай только на основании контекста. "
            "Если данных недостаточно, честно скажи об этом. "
            "Пиши только по-русски, без китайских иероглифов.\n"
            f"{FACTUAL_DISCIPLINE_RU}\n\n"
            f"Контекст:\n{context_block}\n\n"
            f"Вопрос: {question}\n\n"
            "Дай короткий, точный ответ на русском языке."
        )
