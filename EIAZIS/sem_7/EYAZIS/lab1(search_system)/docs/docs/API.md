# API — контракт HTTP

Базовый префикс `/api`. Все ответы — JSON, camelCase НЕ используем
(контракт snake_case). Ошибки:

```json
{ "error": { "code": "not_found", "message": "document 42 not found" } }
```

Коды: 200 ok · 201 created · 400 validation · 404 not_found · 409 conflict ·
503 llm_unavailable. Интерактивная спецификация: Swagger UI `/docs`.

---

## 1. System

### GET /api/health
```json
{
  "status": "ok",
  "db": "ok",
  "index": { "documents": 100, "terms": 4218, "postings": 18740, "embeddings": 100 },
  "llm": { "provider": "mistral", "available": true }
}
```

### GET /api/stats
Агрегаты коллекции: кол-во документов/терминов/постов, средняя длина,
топ-20 терминов по doc_freq, распределение по категориям и годам.

---

## 2. Documents (CRUD + индексация)

### GET /api/documents?category=&q=&page=1&page_size=20
Список с пагинацией (q — подстрочный фильтр по title). Ответ:
`{"items": [DocumentShort...], "total": 100, "page": 1, "page_size": 20}`

### POST /api/documents → 201
```json
{ "title": "Vector databases in production",
  "text": "…≥ 150 слов…",
  "category": "ai_ml", "source": "manual",
  "published_at": "2025-11-03" }
```
Побочный эффект: индексация (postings + embeddings).

### GET /api/documents/{id}
Полный документ + `keywords: [{lemma, weight}]` (top-10 по формуле 1.6) +
`length_lemmas`.

### PUT /api/documents/{id} → переиндексация
### DELETE /api/documents/{id} → 204

### POST /api/documents/upload  (multipart, пачка)
Поле `files[]` (.txt/.md) или `collection.json` (формат COLLECTION.md).
Ответ: `{"added": 12, "skipped": 0, "indexed": 12}`.

### GET /api/documents/{id}/similar?k=5
Похожие документы (dense, cosine) — карточка «Related».

---

## 3. Search

### POST /api/search
```json
{
  "query": "battery storage for renewable energy",
  "model": "bm25",                // boolean|tfidf|bm25|dense|hybrid
  "all_words_together": false,
  "date_start": "2024-01-01",
  "date_end": null,
  "top_k": 10
}
```
Ответ 200:
```json
{
  "query": "battery storage for renewable energy",
  "model": "bm25",
  "search_id": 145,
  "elapsed_ms": 38,
  "results": [
    {
      "document_id": 61,
      "title": "Grid-scale batteries: the missing link",
      "snippet": "Utility-scale battery storage has become the critical…",
      "rank": 12.4371,
      "date": "2025-03-14",
      "matched_terms": ["batteri", "storage", "renewabl", "energi"],
      "highlight_terms": ["battery", "storage", "renewable", "energy"]
    }
  ],
  "llm": { "available": true }
}
```
Контракт `SearchResult` = рис. 3 лабы + обязательные расширения
(matched_terms, highlight_terms). Пустой результат — 200 c `"results": []`
(ошибкой не является).

### GET /api/search/models
Список стратегий с человекочитаемыми названиями для UI.

---

## 4. Metrics

### POST /api/metrics/run
```json
{ "model": "bm25", "top_k": 10 }
```
Прогон по всем 15 qrels-запросам. Ответ — структура из METRICS.md §4.
→ 409, если qrels пусты. Записывает eval_runs + eval_query_results.

### GET /api/metrics/runs?page=1
История прогонов: id, model, created_at, агрегаты.

### GET /api/metrics/runs/{id}
Полный прогон (та же структура, что POST /run).

### GET /api/metrics/compare?run_ids=1,2,3
Массив агрегатов + eleven_point для наложения кривых в UI.

### GET /api/qrels?query_id=
Просмотр эталонной разметки (для страницы Collection → Qrels).

---

## 5. LLM

Все эндпоинты — 503 `llm_unavailable`, если провайдер недоступен.

### POST /api/llm/expand-query
```json
{ "query": "how satellites monitor climate" }
→ { "expanded": ["satellit", "climat", "observ", "earth", "monitor", "temperature"] }
```

### POST /api/llm/answer
```json
{ "query": "why rocket reusability cuts costs", "search_id": 145, "top_n": 5 }
→ {
  "answer": "Rocket reusability reduces launch cost because the first stage… [1] …",
  "citations": [ { "n": 1, "document_id": 88, "title": "Reuse economics" } ]
}
```
Требование к провайдеру: цитировать ТОЛЬКО [n] из выданных документов.

### POST /api/llm/judge
```json
{ "query": "…", "top_n": 10 }
→ { "grades": [ { "document_id": 61, "grade": 3, "reason": "…" } ] }
```
Используется для pseudo-relevance feedback; в эталонные qrels НЕ пишется.

---

## 6. History / Qrels

### GET /api/history?page=1
search_log → `{items: [{id, query_text, model, created_at, elapsed_ms,
top_results}], total}`. Повтор запроса = POST /api/search с теми же полями.

---

## 7. Правила совместимости

- Изменение любого контракта = правка этого файла тем же шагом.
- Frontend не обращается к api по абсолютному URL — только относительный
  `/api/*` (nginx проксирует), см. FRONTEND_RULES.
- pagination: page ≥ 1, page_size ≤ 100.
