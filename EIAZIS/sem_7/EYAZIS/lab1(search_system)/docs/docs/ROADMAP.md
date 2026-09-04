# ROADMAP — этапы реализации

> Правило: работа идёт строго по этапам сверху вниз. Этап закрыт, только
> когда выполнен **весь** его Definition of Done и чекбоксы проставлены.
> Синхронная запись журнала — [PROGRESS.md](PROGRESS.md).

---

## Этап 0 — Скелет репозитория `[ ]`

- [ ] `docker-compose.yml`: сервисы `web`, `api`, `db` (+ профили `local`=ollama, `demo`=pgadmin, `test`=playwright)
- [ ] `.env.example` (все переменные из ARCHITECTURE.md §5, без секретов)
- [ ] `backend/Dockerfile` (python:3.12-slim), `frontend/Dockerfile` (nginx:alpine) + `nginx.conf`
- [ ] Каталоги `backend/app/*`, `frontend/assets/*`, `data/collection`, `data/qrels`
- [ ] `docker compose up --build` поднимается, healthcheck'и зелёные (страницы-заглушки)

**DoD**: одна команда поднимает стек, `/docs` Swagger отвечает, nginx отдаёт index.

---

## Этап 1 — Документация проекта `[x]`

- [x] README.md, AGENTS.md
- [x] ROADMAP.md, PROGRESS.md
- [x] ARCHITECTURE.md, DATABASE.md
- [x] ALGORITHMS.md, METRICS.md
- [x] API.md, FRONTEND_RULES.md
- [x] COLLECTION.md, DECISIONS.md, REPORT_CHECKLIST.md

**DoD**: документация самосогласована, перекрёстные ссылки валидны.

---

## Этап 2 — База данных и тестовые данные `[ ]`

Спецификация: [DATABASE.md](DATABASE.md), [COLLECTION.md](COLLECTION.md).

- [ ] Модуль `db.py`: engine (SQLAlchemy 2 + psycopg), сессии, BASE metadata
- [ ] ORM-модели всех 8 таблиц + `vector(1024)` колонка
- [ ] Alembic-миграция `001_init` (или DDL-скрипт init.sql — по ADR-008)
- [ ] Сид: 100 документов из `data/collection/docs.json`
- [ ] Сид: 15 запросов и qrels из `data/qrels/*.json`
- [ ] Идемпотентность сида (повторный запуск не дублирует)

**DoD**: `SELECT count(*) FROM documents` = 100; qrels ≥ 15 запросов; повторный `up` не ломает данные.

---

## Этап 3 — NLP и индексация `[ ]`

Спецификация: [ALGORITHMS.md §1, §2](ALGORITHMS.md).

- [ ] Препроцессинг: токенизация, lowercase, стоп-слова, WordNet-лемматизация (NLTK)
- [ ] Словарь `terms` + doc_freq, инвертированный индекс `postings`
- [ ] IDF по формуле (1.5), веса TF-IDF по формуле (1.6)
- [ ] Нормированный вектор документа (норм. TF-IDF, формула из лабы)
- [ ] Ключевые слова документа = top-N по весу (1.6) — endpoint `GET /documents/{id}/keywords`
- [ ] Эмбеддинги: mistral-embed (1024) + запись в pgvector; фолбэк — пропуск с warning
- [ ] Реиндексация документа при обновлении/удалении

**DoD**: для документа вручную воспроизводится вес одного термина (hand-check в тесте).

---

## Этап 4 — Поиск: 5 моделей ранжирования `[ ]`

Спецификация: [ALGORITHMS.md §3](ALGORITHMS.md), [API.md §/search](API.md).

- [ ] Класс `Search` (поля лабы: all_words_together, date_start, date_end, search_query)
- [ ] Boolean: AND / фраза («все слова вместе»)
- [ ] TF-IDF + косинус (формулы 1.7–1.8 и нормированное представление)
- [ ] **BM25 (k1=1.2, b=0.75) — основной по варианту**
- [ ] Dense: cosine по pgvector
- [ ] Hybrid: RRF поверх BM25 + Dense
- [ ] SearchResult: snippet 300 симв., подсветка терминов, список найденных слов, rank, дата
- [ ] Фильтры: диапазон дат, top_k; фразовый режим

**DoD**: `curl` каждого режима возвращает корректный JSON; одинаковый запрос даёт осмысленно разный порядок у разных моделей (проверяется тестом).

---

## Этап 5 — Оценка качества (метрики) `[ ]`

Спецификация: [METRICS.md](METRICS.md).

- [ ] Evaluator: P, R, F1, P@5, P@10, R-precision, AP/MAP, MRR, NDCG@10, 11-point интерполяция
- [ ] Прогон по всем 15 запросам qrels для выбранной модели
- [ ] Таблица `eval_runs` (сохранение прогонов), endpoint'ы run/list/compare
- [ ] Данные для UI: PR-кривые по моделям, bar-чарты метрик

**DoD**: MAP и NDCG одного запроса совпадают с hand-computed тестом; прогоны 5 моделей можно сравнить на одном экране (данные API готовы).

---

## Этап 6 — LLM-слой (Mistral + Ollama-фолбэк) `[ ]`

Спецификация: [ARCHITECTURE.md §4](ARCHITECTURE.md), [API.md §llm](API.md).

- [ ] Абстракция `LlmProvider`: mistral | ollama | off, конфиг из env
- [ ] `POST /api/llm/expand-query` — 5–8 ключевых слов для запроса
- [ ] `POST /api/llm/answer` — RAG-ответ по топ-5 с цитатами [n], ≤200 слов
- [ ] `POST /api/llm/judge` — LLM-оценки 0–3 по топ-N → pseudo-relevance feedback
- [ ] Graceful degradation без ключа: 503 c понятным текстом, UI скрывает функции

**DoD**: с ключом — цитаты в ответе соответствуют выданным документам; без ключа — поиск, метрики, CRUD работают как раньше.

---

## Этап 7 — Фронтенд (SPA) `[ ]`

Спецификация: [FRONTEND_RULES.md](FRONTEND_RULES.md) — контракт дизайн-системы.

- [ ] Каркас: index.html, роутер (#/search, #/document/:id, #/metrics, #/collection, #/history, #/help), api-client, состояния
- [ ] Страница поиска: герой с поисковой строкой, чипы моделей, фильтры, выдача (ранг, шкала, snippet, подсветка, список слов), панель LLM-ответа
- [ ] Просмотр документа: полный текст, ключевые слова с весами, кнопка «похожие»
- [ ] Метрики: выбор модели/прогона, таблицы + Chart.js (PR-кривые, bar-чарты), сравнение моделей
- [ ] Коллекция: таблица документов, CRUD-формы, загрузка пачкой
- [ ] History, Help (глоссарий ПОД/ПОЗ, формулы), health-индикатор
- [ ] Клавиатура: `/`, `j/k`, `Enter`, `Esc`; все состояния loading/empty/error

**DoD**: чек-лист FRONTEND_RULES §9 пройден полностью, скриншоты страниц приложены в PROGRESS.

---

## Этап 8 — Тесты и отчётные артефакты `[ ]`

- [ ] pytest unit: препроцессинг, TF-IDF, BM25, RRF, каждая метрика (hand-computed)
- [ ] pytest integration: index→search→metrics на тестовой БД
- [ ] Playwright smoke: поиск → выдача; метрики → графики; CRUD → документ; help
- [ ] Makefile: `up`, `down`, `logs`, `test`, `seed`, `smoke`
- [ ] Экспорт результатов метрик (JSON + PNG-графики) для отчёта
- [ ] Заполнить фактические результаты в REPORT_CHECKLIST.md

**DoD**: `make test` зелёный локально и в контейнере; артефакты метрик лежат в `reports/`.

---

## Этап 9 — Финальная приёмка `[ ]`

- [ ] Чистый прогон: `docker compose down -v && docker compose up --build` с нуля
- [ ] Прогнать все сценарии из REPORT_CHECKLIST.md §3
- [ ] Доступ по LAN с другого устройства (требование варианта)
- [ ] README актуален, документация ↔ код согласованы
- [ ] Финальная запись в PROGRESS.md

**DoD**: система сдаётся одной командой и переживает демонстрацию преподавателю.
