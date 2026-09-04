import requests
import re

from ..config import get_settings


RUSSIAN_ONLY_POLICY = (
    "Отвечай строго на русском языке. "
    "Не используй английские слова, если можно дать русский эквивалент. "
    "Если пользователь пишет на другом языке, всё равно отвечай по-русски."
)


class LlmService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def embed(self, text: str) -> list[float]:
        response = requests.post(
            f"{self.settings.ollama_base_url}/api/embeddings",
            json={"model": self.settings.ollama_embed_model, "prompt": text},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        vector = payload.get("embedding")
        if not vector:
            raise ValueError("Ollama did not return embedding")
        return vector

    def chat(self, prompt: str) -> str:
        return self.chat_messages(
            messages=[{"role": "user", "content": prompt}],
        )

    def chat_messages(self, messages: list[dict[str, str]], system_prompt: str | None = None) -> str:
        payload_messages = []
        if system_prompt:
            payload_messages.append(
                {
                    "role": "system",
                    "content": f"{RUSSIAN_ONLY_POLICY}\n\n{system_prompt}",
                }
            )
        else:
            payload_messages.append({"role": "system", "content": RUSSIAN_ONLY_POLICY})
        payload_messages.extend(messages)

        response = requests.post(
            f"{self.settings.ollama_base_url}/api/chat",
            json={
                "model": self.settings.ollama_chat_model,
                "messages": payload_messages,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        message = payload.get("message") or {}
        content = (message.get("content") or "").strip()
        if not content:
            raise ValueError("Ollama did not return chat content")
        return self._force_russian_rewrite_if_needed(content)

    @staticmethod
    def _latin_words_count(text: str) -> int:
        return len(re.findall(r"\b[A-Za-z]{2,}\b", text))

    @staticmethod
    def _has_suspicious_non_cyrillic_script(text: str) -> bool:
        # Detect cases where the model starts outputting non-Russian scripts (e.g. Chinese).
        # Allow punctuation/digits/whitespace; we only care about letters.
        letters = re.findall(r"[^\W\d_]", text, flags=re.UNICODE)
        if not letters:
            return False
        cyr = sum(1 for ch in letters if "\u0400" <= ch <= "\u04FF")
        non_cyr = len(letters) - cyr
        # If there are at least a few non-Cyrillic letters and they are a noticeable share, rewrite.
        return non_cyr >= 6 and (non_cyr / max(len(letters), 1)) >= 0.08

    def _force_russian_rewrite_if_needed(self, content: str) -> str:
        if self._latin_words_count(content) < 2 and not self._has_suspicious_non_cyrillic_script(content):
            return content

        rewrite_prompt = (
            "Перепиши следующий ответ полностью на русском языке. "
            "Сохрани смысл, но убери английские слова и фразы. "
            "Верни только итоговый текст без комментариев.\n\n"
            f"Текст:\n{content}"
        )
        response = requests.post(
            f"{self.settings.ollama_base_url}/api/chat",
            json={
                "model": self.settings.ollama_chat_model,
                "messages": [
                    {"role": "system", "content": RUSSIAN_ONLY_POLICY},
                    {"role": "user", "content": rewrite_prompt},
                ],
                "stream": False,
            },
            timeout=90,
        )
        response.raise_for_status()
        payload = response.json()
        message = payload.get("message") or {}
        rewritten = (message.get("content") or "").strip()
        if rewritten:
            return rewritten
        return content
