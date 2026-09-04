# IPS «Index Room» — Информационно-поисковая система (Лаба 1.1, вариант 11)

Учебная информационно-поисковая система: индексация естественно-языковых
документов, поиск по ЕЯ-запросу (английский), **вероятностная модель ранжирования
(BM25/RSJ)** как основная по варианту, оценка качества поиска по метрикам ROMIP.

> **Вариант 11**: интерфейс с пользователем · локальная вычислительная сеть ·
> вероятностная стратегия поиска · английский язык.

## Стек

| Слой | Технология |
|---|---|
| Backend | FastAPI + SQLAlchemy 2 + NLTK (лемматизация) |
| Ранжирование | Boolean, TF-IDF (формулы 1.5–1.8 лабы), **BM25 (основной)**, Dense (pgvector), Hybrid (RRF) |
| БД | PostgreSQL 16 + pgvector (инвертированный индекс + эмбеддинги в одной схеме) |
| LLM | Mistral API (основной, ключ в `.env`), Ollama — опциональный офлайн-профиль |
| Frontend | Vanilla JS SPA без сборки, nginx, собственная дизайн-система |
| Запуск | Docker Compose, одна команда |
| Тесты | pytest + Playwright smoke |

## Быстрый старт (после реализации этапов 0–8)

```bash
cp .env.example .env          # вставить MISTRAL_API_KEY (опционально)
docker compose up --build
# SPA:      http://localhost:8080
# API docs: http://localhost:8000/docs
# pgadmin:  docker compose --profile demo up   (для показа БД)
```

Система полностью работоспособна **без** ключа Mistral: LLM-функции
(расширение запроса, RAG-ответ, LLM-judge) деградируют с явным сообщением.

## Карта документации

| Файл | Содержимое | Когда читать |
|---|---|---|
| [AGENTS.md](AGENTS.md) | Правила работы агентов с репозиторием | Перед любым изменением кода |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Этапы работ с чекбоксами — текущее состояние | Всегда, перед началом работы |
| [docs/PROGRESS.md](docs/PROGRESS.md) | Журнал прогресса (что сделано, когда, чем проверено) | Всегда, перед началом работы |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Компоненты, docker-сервисы, потоки данных | Про устройство системы |
| [docs/DATABASE.md](docs/DATABASE.md) | Схема БД, ER-диаграмма, индексы | Работа с БД |
| [docs/ALGORITHMS.md](docs/ALGORITHMS.md) | Формулы 1.5–1.8, BM25/RSJ, RRF, препроцессинг | Любая работа с ранжированием |
| [docs/METRICS.md](docs/METRICS.md) | Метрики качества (ROMIP), формулы, представление в UI | Работа с оценкой качества |
| [docs/API.md](docs/API.md) | Контракт HTTP API | Работа с backend/frontend |
| [docs/FRONTEND_RULES.md](docs/FRONTEND_RULES.md) | Дизайн-система и анти-«нейрослоп» правила | Любая работа с UI |
| [docs/COLLECTION.md](docs/COLLECTION.md) | Тестовая коллекция и qrels | Наполнение данных |
| [docs/METRICS.md](docs/METRICS.md) / [docs/COLLECTION.md](docs/COLLECTION.md) | Математика оценки и данные для неё | Отчёт |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Архитектурные решения (ADR) | «Почему так?» |
| [docs/REPORT_CHECKLIST.md](docs/REPORT_CHECKLIST.md) | Маппинг требований лабы → код | Приёмка, защита |

## Структура репозитория (целевая)

```
07/
├── AGENTS.md, README.md
├── docs/                     # вся документация проекта
├── data/
│   ├── collection/           # тестовая коллекция документов (JSON)
│   └── qrels/                # тестовые запросы + оценки релевантности
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/                  # FastAPI-приложение (см. ARCHITECTURE.md §3)
│   └── tests/                # pytest
├── frontend/
│   ├── Dockerfile, nginx.conf
│   ├── index.html
│   └── assets/               # css/ js/ fonts/ img/
├── docker-compose.yml
└── .env.example
```

`practice.py` — личный черновик владельца, к проекту не относится.
