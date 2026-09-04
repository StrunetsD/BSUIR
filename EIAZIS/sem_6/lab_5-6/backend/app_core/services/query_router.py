import re
from dataclasses import dataclass

from ..repositories.rag_repository import RagRepository

try:
    import pymorphy3  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pymorphy3 = None


@dataclass
class RouteDecision:
    handled: bool
    answer: str | None = None
    confidence: float = 0.0
    route: str = "none"


class QueryRouter:
    def __init__(self) -> None:
        self.repo = RagRepository()
        self._morph = pymorphy3.MorphAnalyzer() if pymorphy3 else None

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "")).strip()

    def _normalize_phrase(self, text: str) -> str:
        cleaned = self._clean(text.lower())
        cleaned = re.sub(r"[^а-яёa-z0-9\s\-]", " ", cleaned)
        cleaned = self._clean(cleaned)
        if not cleaned:
            return ""
        if not self._morph:
            return cleaned
        lemmas: list[str] = []
        for token in cleaned.split():
            parsed = self._morph.parse(token)
            lemmas.append(parsed[0].normal_form if parsed else token)
        return " ".join(lemmas)

    @staticmethod
    def _extract_quoted_title(text: str) -> str | None:
        patterns = [
            r"[«\"“]([^»\"”]{2,120})[»\"”]",
            r"стихотворени[ея]\s+([а-яё0-9\-\s]{3,})",
            r"поэм[аы]\s+([а-яё0-9\-\s]{3,})",
        ]
        lowered = text.lower()
        for pattern in patterns:
            match = re.search(pattern, lowered, re.IGNORECASE)
            if match:
                return QueryRouter._clean(match.group(1))
        return None

    def _extract_author(self, text: str) -> str | None:
        match = re.search(
            r"(?:автор|поэт|писатель|произведени[ея]\s+автора)\s+([а-яё\-]+\s*[а-яё\-]*)",
            text.lower(),
            re.IGNORECASE,
        )
        if match:
            return self._normalize_phrase(match.group(1))
        return None

    @staticmethod
    def _is_author_list_request(text: str) -> bool:
        lowered = text.lower()
        return any(
            marker in lowered
            for marker in ("какие авторы", "список авторов", "авторы в базе", "перечень авторов")
        )

    @staticmethod
    def _is_titles_by_author_request(text: str) -> bool:
        lowered = text.lower()
        return any(
            marker in lowered
            for marker in (
                "какие произведения",
                "какие стихи",
                "что есть у",
                "что в базе по",
                "покажи произведения",
            )
        )

    @staticmethod
    def _is_full_text_request(text: str) -> bool:
        lowered = text.lower()
        return any(
            marker in lowered
            for marker in ("полный текст", "текст стихотворения", "покажи стих", "выведи стих")
        )

    @staticmethod
    def _is_metadata_request(text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in ("кто автор", "кто написал", "информация о", "что за произведение"))

    @staticmethod
    def _is_analysis_request(text: str) -> bool:
        lowered = text.lower()
        markers = (
            "что хотел сказать",
            "что он хотел сказать",
            "что она хотела сказать",
            "что автор хотел сказать",
            "в чем смысл",
            "смысл",
            "идея",
            "тема",
            "проблематик",
            "анализ",
            "разбор",
            "интерпретац",
            "объясни",
        )
        return any(m in lowered for m in markers)

    @staticmethod
    def _wants_document_content(text: str) -> bool:
        """Вопрос о содержимом / тексте документа — отдаём в RAG, а не в короткую meta-ветку."""
        lowered = text.lower()
        markers = (
            "что в ",
            "что в«",
            "что находится",
            "содержимое",
            "содержание",
            "текст документа",
            "приведи текст",
            "покажи текст",
            "фрагмент текста",
            "цитируй из",
            "перескажи по тексту",
            "о чем документ",
            "о чём документ",
            "кратко о документе",
        )
        return any(m in lowered for m in markers)

    @staticmethod
    def _is_author_question(text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in ("кто написал", "кто автор", "чьё произведение", "чье произведение"))

    def _match_author_candidates(self, author_query: str) -> list[dict]:
        raw_candidates = self.repo.find_documents_by_author(author_query, limit=20)
        if raw_candidates:
            return raw_candidates
        normalized_author = self._normalize_phrase(author_query)
        if normalized_author and normalized_author != author_query:
            return self.repo.find_documents_by_author(normalized_author, limit=20)
        return []

    def route(self, user_text: str) -> RouteDecision:
        text = self._clean(user_text)
        if not text:
            return RouteDecision(handled=True, answer="Введите вопрос по русской литературе.", confidence=1.0, route="empty")

        if self._is_author_list_request(text):
            authors = self.repo.list_authors(limit=100)
            if not authors:
                return RouteDecision(
                    handled=True,
                    answer="В базе пока нет авторов. Сначала загрузите документы.",
                    confidence=0.98,
                    route="authors:list",
                )
            return RouteDecision(
                handled=True,
                answer="Авторы в базе: " + ", ".join(authors[:25]) + ("." if len(authors) <= 25 else ", ..."),
                confidence=0.99,
                route="authors:list",
            )

        author = self._extract_author(text)
        if author and self._is_titles_by_author_request(text):
            docs = self._match_author_candidates(author)
            if not docs:
                return RouteDecision(
                    handled=True,
                    answer=f"По автору '{author}' в структурной БД ничего не найдено.",
                    confidence=0.9,
                    route="author:works",
                )
            lines = [f"- {doc['title']}" for doc in docs]
            return RouteDecision(
                handled=True,
                answer=f"Найдены произведения автора '{author}':\n" + "\n".join(lines),
                confidence=0.96,
                route="author:works",
            )

        title = self._extract_quoted_title(text)
        if title and self._is_full_text_request(text):
            doc = self.repo.find_document_by_title_candidates(title, self._normalize_phrase(title))
            if not doc:
                return RouteDecision(handled=False, confidence=0.2, route="title:fulltext")
            raw_text = (doc.get("raw_text") or "").strip()
            if not raw_text:
                return RouteDecision(
                    handled=True,
                    answer=f"Документ '{doc['title']}' найден, но полный текст пуст. Попробуйте переингестировать файл.",
                    confidence=0.95,
                    route="title:fulltext",
                )
            excerpt = raw_text[:2200]
            suffix = "\n\n[Текст обрезан для ответа. Могу продолжить следующей частью.]" if len(raw_text) > 2200 else ""
            author_label = doc.get("author") or "не указан"
            return RouteDecision(
                handled=True,
                answer=f"Найдено в БД: «{doc['title']}» (автор: {author_label}).\n\n{excerpt}{suffix}",
                confidence=0.98,
                route="title:fulltext",
            )

        if title:
            doc = self.repo.find_document_by_title_candidates(title, self._normalize_phrase(title))
            if doc:
                author_label = doc.get("author") or "не указан"
                source_label = doc.get("source") or "не указан"
                # For analysis-type questions, prefer RAG+LLM (needs context + synthesis), not router meta.
                if self._is_analysis_request(text):
                    return RouteDecision(handled=False, confidence=0.0, route="analysis:delegate")
                if self._wants_document_content(text):
                    return RouteDecision(handled=False, confidence=0.0, route="title:content-delegate")
                if self._is_author_question(text):
                    return RouteDecision(
                        handled=True,
                        answer=f"«{doc['title']}» написал {author_label}.",
                        confidence=0.99,
                        route="title:author",
                    )
                return RouteDecision(
                    handled=True,
                    answer=(
                        f"В структурной БД найден документ: «{doc['title']}».\n"
                        f"Автор: {author_label}.\nИсточник: {source_label}."
                    ),
                    confidence=0.96,
                    route="title:meta",
                )
            if self._is_author_question(text):
                # If the work is not indexed as a separate document title, do not hard-stop the dialog:
                # fall back to RAG+LLM (still constrained by domain prompts).
                return RouteDecision(handled=False, confidence=0.35, route="title:author-not-found")

        if self._is_metadata_request(text):
            text_hits = self.repo.search_raw_text(text, limit=1)
            if text_hits:
                row = text_hits[0]
                return RouteDecision(
                    handled=True,
                    answer=f"Похоже, речь о «{row['title']}» ({row.get('author') or 'автор не указан'}).",
                    confidence=0.82,
                    route="text:meta",
                )

        text_hits = self.repo.search_raw_text(text, limit=3)
        if text_hits:
            lines = [
                f"- «{row['title']}» ({row.get('author') or 'автор не указан'})"
                for row in text_hits
            ]
            return RouteDecision(
                handled=True,
                answer="Нашел совпадения в структурной БД:\n" + "\n".join(lines),
                confidence=0.72,
                route="text:search",
            )

        return RouteDecision(handled=False, confidence=0.0, route="fallback")
