import re

from ..domain import AUTHOR_FACTS, BOOKS, HELP_TEXT, Book


class DialogService:
    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()

    def _book_by_title(self, text: str) -> Book | None:
        for book in BOOKS:
            if self._normalize(book.title) in text:
                return book
        return None

    def _books_by_author(self, text: str) -> list[Book]:
        found = []
        for book in BOOKS:
            author_tokens = self._normalize(book.author).split()
            if any(token in text for token in author_tokens):
                found.append(book)
        return found

    @staticmethod
    def _recommend(text: str) -> list[Book]:
        if "психолог" in text:
            return [book for book in BOOKS if "психолог" in book.genre]
        if "эпопе" in text:
            return [book for book in BOOKS if "эпопея" in book.genre]
        if "сатир" in text:
            return [book for book in BOOKS if "поэма" in book.genre]
        return []

    def generate_response(self, user_text: str) -> str:
        text = self._normalize(user_text)

        if not text:
            return "Введите сообщение, чтобы продолжить диалог."
        if any(marker in text for marker in ("привет", "здравств", "добрый")):
            return "Здравствуйте! Я диалоговая система по домену 'литература'."
        if "помощ" in text or "help" in text:
            return HELP_TEXT

        if "кто такой" in text or "об авторе" in text:
            for key, value in AUTHOR_FACTS.items():
                if key in text:
                    return value
            return "Уточните автора. Поддерживаются: Пушкин, Достоевский, Толстой, Лермонтов, Гоголь."

        if any(marker in text for marker in ("книги автора", "покажи книги", "что написал")):
            books = self._books_by_author(text)
            if not books:
                return "Не смог найти книги этого автора в базе."
            return "Книги: " + "; ".join(f"{book.title} ({book.year})" for book in books) + "."

        if any(marker in text for marker in ("жанр", "описание", "о чем", "о чём")):
            book = self._book_by_title(text)
            if book is None:
                return "Укажите название книги полностью."
            return f"{book.title}: жанр - {book.genre}. {book.description}"

        if any(marker in text for marker in ("рекоменд", "посоветуй", "что почитать")):
            recs = self._recommend(text)
            if recs:
                return "Рекомендую: " + "; ".join(f"{book.title} ({book.author})" for book in recs) + "."
            return "Рекомендую начать с 'Евгения Онегина' и 'Преступления и наказания'."

        if any(marker in text for marker in ("спасибо", "благодар")):
            return "Рад помочь. Если нужно, подберу книги по жанру или автору."

        return "Не распознал намерение. Введите 'помощь', чтобы увидеть примеры запросов."
