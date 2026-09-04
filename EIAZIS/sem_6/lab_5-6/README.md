# Лабораторная работа 6 (вариант 6, домен "Литература")

Диалоговая система с поддержкой естественного языка на стеке:

- фронтенд: React + Vite (`project`);
- бэкенд API: Flask (`backend`);
- БД: PostgreSQL (`db` в Docker Compose);
- векторная БД: Qdrant (`qdrant`);
- LLM + embeddings: Ollama **на хосте** (рекомендуется на Mac — Metal); backend в Docker ходит на `host.docker.internal:11434`.

## Что реализовано

- графический интерфейс диалога (оставлен ваш фронтенд);
- отправка запросов из фронтенда в API (`/api/chat`);
- хранение истории диалога в PostgreSQL;
- загрузка истории при открытии страницы;
- очистка истории через API;
- RAG ingest в векторную БД (`/api/rag/ingest`);
- RAG upload файлов (`/api/rag/upload`);
- просмотр загруженных документов (`/api/rag/documents`);
- RAG query с генерацией ответа LLM (`/api/rag/query`);
- контейнеризация всех компонентов (`frontend`, `backend`, `db`).

## Структура

- `project` - фронтенд;
- `backend` - Flask API и логика ответов;
- `qdrant` - хранение эмбеддингов чанков;
- Ollama — локально на машине (не в Compose);
- `docker-compose.yml` — Postgres, Qdrant, backend, frontend.

## Примечание по Mac (M4 и др.)

- CUDA на macOS недоступна; **нативный** Ollama для Apple Silicon использует **Metal** (ускорение на GPU кристалле).
- Контейнерный Ollama на Mac чаще идёт на **CPU**; поэтому по умолчанию backend обращается к **`http://host.docker.internal:11434`** — к Ollama, запущенному **на macOS**.

### Ollama на хосте (терминал)

Установите [Ollama для macOS](https://ollama.com/download). Дальше — только команды в терминале.

**Включить Ollama как сервис (Homebrew):**

```bash
brew services start ollama
```

**Выключить:**

```bash
brew services stop ollama
```

Если ставили не через brew, можно вручную в отдельном окне: `ollama serve` (останов — Ctrl+C).

**Проверка, что API слушает порт 11434:**

```bash
curl -sS http://127.0.0.1:11434/api/tags
```

**Модели (один раз):**

```bash
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

### Запуск стека Docker

Из каталога `lab_5-6`:

```bash
docker compose up -d --build
```

Остановка контейнеров: `docker compose down` (см. раздел «Остановка» ниже).

Backend в Docker достучится до Ollama на хосте по `host.docker.internal` (в compose: `extra_hosts: host.docker.internal:host-gateway`).

**Важно:** если раньше поднимали Ollama в Docker на `:11434`, остановите тот контейнер, иначе порт займёт контейнер, а не хостовый Ollama.

После запуска:

- фронтенд: [http://localhost:5174](http://localhost:5174)
- бэкенд API: [http://localhost:5001/api/health](http://localhost:5001/api/health)
- PostgreSQL: `localhost:5433`  
  user: `literature`, password: `literature`, db: `literature_lab6`
- Qdrant: [http://localhost:6333](http://localhost:6333)
- Ollama на хосте: [http://localhost:11434](http://localhost:11434)

Модели по умолчанию в `docker-compose.yml`:

- `qwen2.5:7b-instruct` (чат)
- `nomic-embed-text` (эмбеддинги)

## RAG API (пример)

Индексирование документа:

```bash
curl -X POST http://localhost:5001/api/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Евгений Онегин (фрагмент)",
    "author":"Александр Пушкин",
    "source":"manual",
    "text":"Мой дядя самых честных правил..."
  }'
```

Загрузка документа файлом (TXT/UTF-8 или cp1251):

```bash
curl -X POST http://localhost:5001/api/rag/upload \
  -F "file=@/path/to/brodsky.txt" \
  -F "title=Натюрморт" \
  -F "author=Иосиф Бродский" \
  -F "source=poetry_upload"
```

Список загруженных документов:

```bash
curl "http://localhost:5001/api/rag/documents?limit=50"
```

Вопрос к RAG:

```bash
curl -X POST http://localhost:5001/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question":"О чем этот фрагмент?",
    "top_k":4
  }'
```

## Остановка

```bash
docker compose down
```

С удалением volume БД:

```bash
docker compose down -v
```

## Backend структура (best practices)

`backend/app_core`:

- `config.py` - конфиг через Pydantic Settings;
- `bootstrap.py` - инициализация таблиц и retry при старте;
- `db.py` - подключение к PostgreSQL;
- `vector_store.py` - клиент и коллекция Qdrant;
- `schemas.py` - валидация входных/выходных payload;
- `domain.py` - доменные данные литературы;
- `repositories/` - доступ к данным (chat/rag);
- `services/` - бизнес-логика диалога, LLM и RAG;
- `rag_pipeline/` - поэтапный RAG pipeline (chunking, embedding, prompt, orchestrator);
- `api/` - Flask Blueprints (health/chat/rag).
