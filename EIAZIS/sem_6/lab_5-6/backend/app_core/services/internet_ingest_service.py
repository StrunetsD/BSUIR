import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import urlparse

import requests

from .rag_service import RagService


@dataclass
class UrlIngestItem:
    url: str
    title: str | None = None
    author: str | None = None
    source: str | None = None


class InternetIngestService:
    def __init__(self) -> None:
        self.rag = RagService()

    @staticmethod
    def _strip_html(html: str) -> str:
        text = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        text = unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _derive_title(url: str, html: str) -> str:
        match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
        if match:
            title = re.sub(r"\s+", " ", unescape(match.group(1))).strip()
            if title:
                return title[:220]
        parsed = urlparse(url)
        tail = parsed.path.rstrip("/").split("/")[-1]
        return tail or parsed.netloc or "web_document"

    @staticmethod
    def _is_http(url: str) -> bool:
        return url.startswith("http://") or url.startswith("https://")

    def ingest_urls(self, items: list[UrlIngestItem], max_chars_per_doc: int = 12000) -> dict:
        results: list[dict] = []
        success = 0
        failed = 0

        for item in items:
            url = (item.url or "").strip()
            if not url or not self._is_http(url):
                failed += 1
                results.append({"url": url, "ok": False, "error": "Only http/https URLs are supported"})
                continue

            try:
                response = requests.get(
                    url,
                    timeout=20,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"
                        )
                    },
                )
                response.raise_for_status()
                html = response.text
                extracted_text = self._strip_html(html)
                extracted_text = extracted_text[:max_chars_per_doc].strip()
                if len(extracted_text) < 300:
                    raise ValueError("Extracted text is too short")

                title = (item.title or self._derive_title(url, html)).strip()
                source = (item.source or "web").strip()
                author = (item.author or None)

                ingest_result = self.rag.ingest(
                    title=title,
                    source=source,
                    author=author,
                    text=extracted_text,
                )
                success += 1
                results.append(
                    {
                        "url": url,
                        "ok": True,
                        "title": title,
                        "chars": len(extracted_text),
                        "document": ingest_result.get("document", {}),
                    }
                )
            except Exception as exc:
                failed += 1
                results.append({"url": url, "ok": False, "error": str(exc)})

        return {
            "ok": failed == 0,
            "success": success,
            "failed": failed,
            "results": results,
        }
