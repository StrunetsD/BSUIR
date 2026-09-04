# DATABASE — схема PostgreSQL 16 + pgvector

## 1. ER-диаграмма

```mermaid
erDiagram
    DOCUMENTS ||--o{ POSTINGS : "has"
    TERMS ||--o{ POSTINGS : "indexed by"
    DOCUMENTS ||--|| DOCUMENT_EMBEDDINGS : "embedded"
    DOCUMENTS ||--o{ QRELS : "judged"
    QUERIES ||--o{ QRELS : "has"
    QUERIES ||--o{ EVAL_QUERY_RESULTS : "evaluated"
    EVAL_RUNS ||--o{ EVAL_QUERY_RESULTS : "contains"
    SEARCH_LOG }o--|| DOCUMENTS : "results(jsonb)"

    DOCUMENTS {
        int id PK
        text title
        text text
        text category
        text lang
        text source
        date published_at
        timestamptz added_at
    }
    TERMS {
        int id PK
        text lemma UK
        text lang
        int doc_freq
    }
    POSTINGS {
        int document_id FK
        int term_id FK
        int tf
        real idf
        real tfidf_weight
        real tfidf_norm
    }
    DOCUMENT_EMBEDDINGS {
        int document_id PK_FK
        vector embedding
        text model
    }
    QUERIES {
        int id PK
        text text
        text topic
        text note
    }
    QRELS {
        int query_id FK
        int document_id FK
        int grade
    }
    SEARCH_LOG {
        int id PK
        text query_text
        text model
        jsonb params
        jsonb results
        int elapsed_ms
        timestamptz created_at
    }
    EVAL_RUNS {
        int id PK
        text model
        jsonb params
        jsonb metrics
        timestamptz created_at
    }
    EVAL_QUERY_RESULTS {
        int run_id FK
        int query_id FK
        jsonb per_query
    }
```

## 2. Таблицы (канонический DDL)

DDL хранится в `backend/db/init.sql`, применяется контейнером `db` при
первом старте (`docker-entrypoint-initdb.d`). Расширение:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### documents — коллекция
```sql
CREATE TABLE documents (
    id            serial PRIMARY KEY,
    title         text NOT NULL,
    text          text NOT NULL,
    category      text NOT NULL,
    lang          text NOT NULL DEFAULT 'en',
    source        text NOT NULL,
    published_at  date NOT NULL,
    added_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_documents_published ON documents(published_at);
```

### terms — словарь D
```sql
CREATE TABLE terms (
    id        serial PRIMARY KEY,
    lemma     text NOT NULL UNIQUE,
    lang      text NOT NULL DEFAULT 'en',
    doc_freq  int  NOT NULL DEFAULT 0
);
```
`doc_freq` = P_i из формулы (1.5); N = `count(documents)`.

### postings — инвертированный индекс
```sql
CREATE TABLE postings (
    document_id  int  NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    term_id      int  NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    tf           int  NOT NULL,
    idf          real NOT NULL,          -- B_i, формула (1.5)
    tfidf_weight real NOT NULL,          -- A_i^j, формула (1.6)
    tfidf_norm   real NOT NULL,          -- нормированный вес (§2.3 ALGORITHMS)
    PRIMARY KEY (document_id, term_id)
);
CREATE INDEX idx_postings_term ON postings(term_id);
```

### document_embeddings — pgvector
```sql
CREATE TABLE document_embeddings (
    document_id int PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    embedding   vector(1024) NOT NULL,
    model       text NOT NULL
);
CREATE INDEX idx_emb_hnsw ON document_embeddings
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

### queries + qrels — эталонная разметка
```sql
CREATE TABLE queries (
    id    serial PRIMARY KEY,
    text  text NOT NULL UNIQUE,
    topic text NOT NULL,
    note  text
);
CREATE TABLE qrels (
    query_id    int NOT NULL REFERENCES queries(id) ON DELETE CASCADE,
    document_id int NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    grade       int NOT NULL CHECK (grade BETWEEN 0 AND 3),
    PRIMARY KEY (query_id, document_id)
);
```
`grade`: 0 — нерелевантен, 1 — маргинально, 2 — релевантен, 3 —
полностью релевантен (для бинарных метрик релевантность = grade ≥ 2).

### search_log — история запросов
```sql
CREATE TABLE search_log (
    id          serial PRIMARY KEY,
    query_text  text  NOT NULL,
    model       text  NOT NULL,        -- boolean|tfidf|bm25|dense|hybrid
    params      jsonb NOT NULL,        -- top_k, all_words_together, dates
    results     jsonb NOT NULL,        -- [{document_id, rank}...]
    elapsed_ms  int   NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
```

### eval_runs + eval_query_results — прогоны оценки
```sql
CREATE TABLE eval_runs (
    id         serial PRIMARY KEY,
    model      text NOT NULL,
    params     jsonb NOT NULL,           -- версия индекса, top_k и т.п.
    metrics    jsonb NOT NULL,           -- агрегаты из METRICS.md
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE eval_query_results (
    run_id    int  NOT NULL REFERENCES eval_runs(id) ON DELETE CASCADE,
    query_id  int  NOT NULL REFERENCES queries(id),
    per_query jsonb NOT NULL,            -- P@5/10, AP, NDCG, RR, R-prec
    PRIMARY KEY (run_id, query_id)
);
```

## 3. Инварианты (проверяются кодом/тестами)

1. `postings.tfidf_weight = tf * idf` — всегда (formula 1.6).
2. `terms.doc_freq` = точное число документов с леммой.
3. Удаление документа каскадно чистит postings, embeddings, qrels этого
   документа; eval_runs остаются (исторические, помечены датой).
4. Поиск работает и при пустой таблице embeddings (модели dense/hybrid
   возвращают пустой/деградированный результат с предупреждением в ответе).
5. idf = ln(N / doc_freq) > 0; если лемма есть у всех документов —
   idf ≈ 0 и термин не влияет на ранжирование.

## 4. Правила изменения схемы

Любое изменение таблиц = правка этого файла + init.sql одним шагом
(миграций Alembic на этапе 2 достаточно для старта; переезд на Alembic —
см. ADR-008).
