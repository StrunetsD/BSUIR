import re

from ..repositories.rag_repository import RagRepository
from ..rag_pipeline.pipeline import RagPipeline
from ..rag_pipeline.stages import FACTUAL_DISCIPLINE_RU
from ..rag_pipeline.types import SourceDocument
from ..config import get_settings
from .llm_service import LlmService
from .query_router import QueryRouter

_LIT_POSITIVE_MARKERS = (
    "русск",
    "литератур",
    "поэт",
    "писател",
    "автор",
    "фамилия",
    "советск",
    "роман",
    "повест",
    "рассказ",
    "стих",
    "стихотвор",
    "рифм",
    "проза",
    "лирик",
    "эпос",
    "драма",
    "пушкин",
    "гогол",
    "достоев",
    "толст",
    "чехов",
    "лермонтов",
    "тургенев",
    "бродск",
    "рыж",
    "мандельшт",
    "пастернак",
    "есенин",
    "ахматов",
    "цветаев",
    "символизм",
    "реализм",
    "романтизм",
    "серебряный век",
    "золотой век",
    "онегин",
    "обломов",
    "мертвые души",
    "преступление и наказание",
    "война и мир",
    "кто такой",
    "кто такая",
    "кто это",
    "биограф",
)
_LIT_ANALYSIS_MARKERS = (
    "что хотел сказать",
    "что он хотел сказать",
    "что она хотела сказать",
    "что автор хотел сказать",
    "про что",
    "о чем",
    "о чём",
    "в чем смысл",
    "смысл",
    "идея",
    "тема",
    "проблематик",
    "анализ",
    "разбор",
    "интерпретац",
    "образ",
    "мотив",
    "символ",
    "композици",
    "лирическ",
    "герой",
)
_LIT_NEGATIVE_MARKERS = (
    "политик",
    "эконом",
    "бирж",
    "крипт",
    "биткоин",
    "битко",
    "эфириум",
    "футбол",
    "хоккей",
    "баскетбол",
    "погод",
    "медици",
    "диагноз",
    "рецепт",
    "программир",
    "код",
    "java",
    "python",
    "docker",
    "sql",
    "итал",
    "герман",
    "франц",
    "сша",
    "китай",
    "геополит",
    "выбор",
    "парламент",
    "налог",
    "инфляц",
)
_LIT_THREAD_SIGNALS = (
    "литератур",
    "писател",
    "поэт",
    "роман",
    "повест",
    "рассказ",
    "автор",
    "произведен",
    "достоев",
    "пушкин",
    "толст",
    "анализ",
    "русск",
    "советск",
    "классик",
    "творчеств",
)

class RagService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.repo = RagRepository()
        self.pipeline = RagPipeline()
        self.llm = LlmService()
        self.router = QueryRouter()

    def ingest(self, title: str, source: str | None, text: str, author: str | None = None) -> dict:
        return self.pipeline.ingest_document(
            SourceDocument(
                title=title,
                source=source,
                author=author,
                text=text,
            )
        )

    def query(self, question: str, top_k: int = 4) -> dict:
        return self.pipeline.query(question=question, top_k=top_k)

    @staticmethod
    def _is_in_russian_literature_domain(question: str) -> bool:
        text = question.lower()

        has_positive = any(marker in text for marker in _LIT_POSITIVE_MARKERS)
        has_analysis = any(marker in text for marker in _LIT_ANALYSIS_MARKERS)
        has_negative = any(marker in text for marker in _LIT_NEGATIVE_MARKERS)

        if has_positive:
            return True
        if has_negative:
            return False
        if has_analysis:
            return True

        return False

    @staticmethod
    def _thread_continues_literature(question: str, history: list[dict]) -> bool:
        """Короткий ответ после явно литературного обмена — не отбрасывать как «не по теме»."""
        if not history:
            return False
        q = question.lower().strip()
        if len(q) > 220:
            return False
        if any(marker in q for marker in _LIT_NEGATIVE_MARKERS):
            return False
        last = history[-1]
        snippet = " ".join(
            [
                (last.get("user_text") or "").lower(),
                (last.get("bot_text") or "").lower(),  
            ]
        )
        return any(sig in snippet for sig in _LIT_THREAD_SIGNALS)

    def _in_domain_for_chat(self, question: str, history: list[dict]) -> bool:
        if self._is_in_russian_literature_domain(question):
            return True
        return self._thread_continues_literature(question, history)

    @staticmethod
    def _retrieval_question(question: str) -> str:
        """Усиливает семантику поиска для биографических вопросов (только для эмбеддинга)."""
        ql = question.lower()
        if re.search(r"кто такой|кто такая|кто это такой|биограф", ql):
            return (
                f"{question}\n"
                "Дополнительно для поиска: русский или советский писатель, биография, "
                "творчество, известные произведения."
            )
        return question

    @staticmethod
    def _author_bio_top_k(base_top_k: int, question: str) -> int:
        ql = question.lower()
        if re.search(r"кто такой|кто такая|кто это такой|биограф", ql):
            return max(base_top_k, 8)
        return base_top_k

    @staticmethod
    def _extract_last_quoted_title_from_history(history: list[dict]) -> str | None:
        # Looks for «...», "...", in recent user/bot messages.
        patterns = (r"[«\"]([^»\"]{2,120})[»\"]",)
        for item in reversed(history):
            for key in ("user_text", "bot_text"):
                text = (item.get(key) or "").strip()
                if not text:
                    continue
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        title = match.group(1).strip()
                        if title:
                            return title
        return None

    @staticmethod
    def _looks_like_followup(question: str) -> bool:
        lowered = question.lower().strip()
        markers = (
            "что он",
            "что она",
            "что хотел",
            "что автор хотел",
            "а что",
            "почему",
            "зачем",
            "в чем смысл",
            "объясни",
            "раскрой",
            "сделай анализ",
            "разбор",
            "идея",
            "тема",
        )
        return any(m in lowered for m in markers)

    def _augment_followup_with_title(self, question: str, history: list[dict]) -> str:
        if not self._looks_like_followup(question):
            return question
        # If already contains a quoted title, do nothing.
        if re.search(r"[«\"].+[»\"]", question):
            return question
        last_title = self._extract_last_quoted_title_from_history(history)
        if not last_title:
            return question
        return f"{question}\n\nКонтекст: речь о произведении «{last_title}»."

    @staticmethod
    def _domain_refusal() -> str:
        return (
            "Я отвечаю только по русской литературе. "
            "Задайте вопрос о русских авторах, произведениях, литературных направлениях "
            "или анализе текста."
        )

    @staticmethod
    def _is_verbatim_poem_request(question: str) -> bool:
        text = question.lower()
        markers = (
            "полный текст",
            "полностью",
            "целиком",
            "дословно",
            "точный текст",
            "напиши стихотворение",
            "приведи стихотворение",
            "дай текст стихотворения",
        )
        return any(marker in text for marker in markers)

    @staticmethod
    def _verbatim_refusal() -> str:
        return (
            "Я не выдаю полный текст стихотворения дословно. "
            "Но могу дать краткий пересказ, анализ, тему, мотивы, "
            "разбор образов и историко-литературный контекст произведения."
        )

    def ask(self, question: str, top_k: int = 4) -> dict:
        routed = self.router.route(question)
        if routed.handled and routed.confidence >= self.settings.sql_router_min_confidence:
            return {"answer": routed.answer or "", "contexts": [], "top_k": top_k}

        if self._is_verbatim_poem_request(question):
            return {"answer": self._verbatim_refusal(), "contexts": [], "top_k": top_k}
        if not self._is_in_russian_literature_domain(question):
            return {"answer": self._domain_refusal(), "contexts": [], "top_k": top_k}

        eff_top_k = self._author_bio_top_k(top_k, question)
        contexts = self.pipeline.retrieve_contexts(
            question=self._retrieval_question(question),
            top_k=eff_top_k,
        )
        if contexts:
            answer = self.pipeline.answer_with_context(question=question, contexts=contexts)
            return {"answer": answer, "contexts": contexts, "top_k": top_k}

        fallback_prompt = (
            "Ты диалоговый ассистент только по русской литературе. "
            "Отвечай только в рамках русской литературы (авторы, произведения, эпохи, направления, анализ). "
            "Если запрос не относится к русской литературе, вежливо откажись и попроси задать вопрос по теме.\n"
            f"{FACTUAL_DISCIPLINE_RU}"
        )
        answer = self.llm.chat_messages(
            messages=[{"role": "user", "content": question}],
            system_prompt=fallback_prompt,
        )
        return {"answer": answer, "contexts": [], "top_k": top_k}

    def ask_with_history(self, question: str, history: list[dict], top_k: int = 4) -> dict:
        original_question = question
        is_followup = self._looks_like_followup(original_question)
        question = self._augment_followup_with_title(original_question, history)

        # Router is great for factual lookups, but for follow-up analysis questions it tends to be too "dry".
        # For those, prefer RAG+LLM with history+context even if a matching document exists.
        if not is_followup:
            routed = self.router.route(question)
            if routed.handled and routed.confidence >= self.settings.sql_router_min_confidence:
                return {"answer": routed.answer or "", "contexts": [], "top_k": top_k}

        if self._is_verbatim_poem_request(question):
            return {"answer": self._verbatim_refusal(), "contexts": [], "top_k": top_k}
        if not self._in_domain_for_chat(original_question, history):
            return {"answer": self._domain_refusal(), "contexts": [], "top_k": top_k}

        eff_top_k = self._author_bio_top_k(top_k, question)
        contexts = self.pipeline.retrieve_contexts(
            question=self._retrieval_question(question),
            top_k=eff_top_k,
        )

        history_messages: list[dict[str, str]] = []
        for item in history:
            user_text = (item.get("user_text") or "").strip()
            bot_text = (item.get("bot_text") or "").strip()
            if user_text:
                history_messages.append({"role": "user", "content": user_text})
            if bot_text:
                history_messages.append({"role": "assistant", "content": bot_text})
        history_messages.append({"role": "user", "content": question})

        if contexts:
            context_block = "\n\n".join(
                [
                    (
                        f"[Документ: {ctx['title']}; автор: {ctx.get('author') or 'не указан'}; "
                        f"chunk={ctx['chunk_index']}; score={ctx['score']:.3f}]\n{ctx['chunk_text']}"
                    )
                    for ctx in contexts
                ]
            )
            system_prompt = (
                "Ты диалоговый ассистент только по русской литературе. "
                "Используй историю диалога и контекст из базы знаний. "
                "Отвечай только по русской литературе. "
                "Если вопрос выходит за эту область, вежливо откажись. "
                "Если в контексте нет ответа, прямо скажи об этом.\n"
                f"{FACTUAL_DISCIPLINE_RU}\n\n"
                f"Контекст базы знаний:\n{context_block}"
            )
            answer = self.llm.chat_messages(messages=history_messages, system_prompt=system_prompt)
            return {"answer": answer, "contexts": contexts, "top_k": top_k}

        fallback_prompt = (
            "Ты диалоговый ассистент только по русской литературе. Используй историю диалога. "
            "Если вопрос не по русской литературе, вежливо откажись. "
            "Если вопрос требует точного цитирования или разбора по загруженным текстам, "
            "предложи пользователю загрузить документы в базу знаний.\n"
            f"{FACTUAL_DISCIPLINE_RU}"
        )
        answer = self.llm.chat_messages(messages=history_messages, system_prompt=fallback_prompt)
        return {"answer": answer, "contexts": [], "top_k": top_k}

    def list_documents(self, limit: int = 100) -> list[dict]:
        return self.repo.list_documents(limit=limit)
