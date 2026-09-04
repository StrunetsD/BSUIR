# COLLECTION — тестовая коллекция и эталонная разметка

> Требование лабы: «информация о тестовой коллекции документов» в отчёте.
> Коллекция английская (вариант 11), хранится в репозитории — детерминированная
> и воспроизводимая.

## 1. Состав

| Параметр | Значение |
|---|---|
| Объём | 100 документов |
| Язык | английский |
| Длина документа | 150–400 слов |
| Тематик | 8 × 12–13 документов |
| Источник | составляется вручную/с помощью LLM на этапе 2, затем фиксирован в репо |
| Файл | `data/collection/docs.json` |

### Темы (category-коды)

| category | Тема | Документов |
|---|---|---|
| `ai_ml` | Машинное обучение и нейросети | 13 |
| `space` | Космос и спутники | 13 |
| `climate` | Климат и экология | 12 |
| `cybersec` | Кибербезопасность и криптография | 12 |
| `medicine` | Медицина и биотехнологии | 13 |
| `economy` | Экономика и рынки | 12 |
| `robotics` | Роботы и автономные системы | 12 |
| `energy` | Энергетика и ВИЭ | 13 |

Правила качества текстов:
- реалистичные «статьи», не телеграфные фразы; без повторов предложений
  между документами одной темы (иначе метрики выродятся);
- **пограничные документы обязательны**: 1–2 на тему, которые упоминают
  термины соседней темы (это создаёт честные FP для метрик);
- уникальные заголовки; source — вымышленный (Technical Digest, Wire Archive,
  Field Notes), published_at разбросан по 2023–2026.

## 2. Формат `data/collection/docs.json`

```json
[
  {
    "ext_id": "d001",
    "title": "Contrastive learning beyond images",
    "text": "Contrastive pretraining has moved…",
    "category": "ai_ml",
    "source": "Technical Digest",
    "published_at": "2024-06-11"
  }
]
```
`ext_id` стабилен; числовой `id` назначает БД при сидировании.

## 3. Тестовые запросы и qrels — `data/qrels/`

### queries.json (15 запросов, ЕЯ, английский)

| id | query | topic | ожидаемая тема |
|---|---|---|---|
| q01 | neural network training techniques | ai_ml | ai_ml |
| q02 | satellite earth observation climate data | space | space/climate |
| q03 | renewable energy grid storage batteries | energy | energy |
| q04 | ransomware attack defense strategies | cybersec | cybersec |
| q05 | CRISPR gene editing therapy trials | medicine | medicine |
| q06 | central bank inflation interest policy | economy | economy |
| q07 | warehouse robot path planning | robotics | robotics |
| q08 | solar panel efficiency improvements | energy | energy |
| q09 | phishing detection machine learning | cybersec | cybersec/ai_ml |
| q10 | quantum computing threat to cryptography | cybersec | cybersec |
| q11 | vaccine cold chain logistics | medicine | medicine |
| q12 | rocket reusability launch cost | space | space |
| q13 | deep learning medical imaging diagnosis | medicine | medicine/ai_ml |
| q14 | autonomous vehicle sensor fusion | robotics | robotics |
| q15 | carbon capture technology cost | climate | climate |

### qrels.json — градуированная разметка

```json
[
  { "query": "q01", "judgments": [
    { "ext_id": "d007", "grade": 3 },
    { "ext_id": "d012", "grade": 2 },
    { "ext_id": "d031", "grade": 1 }
  ]}
]
```

Правила разметки:
- на запрос 8–14 оценённых документов; grade: 0/1/2/3
  (2–3 = релевантен для бинарных метрик — см. METRICS.md §1);
- в каждом запросе есть grade 1 «ловушки» (пограничные документы) —
  они снижают честную точность и делают кривые моделей разными;
- полная разметка (grade 0) не требуется: неразмеченное = 0 по правилам TREC,
  но **все** документы темы-«ожидаемая тема» должны быть размечены явно
  (иначе R_total занижен);
- разметку составлять по стратегии: сначала BM25-выдача топ-30 + Dense
  топ-30 объединить, размечать объединение (пул), затем руками добор
  релевантных, которые модели пропустили.

## 4. Статистика для отчёта (заполняется на этапе 2)

| Показатель | Значение |
|---|---|
| Документов | 100 |
| Уникальных лемм (мощность D) | — |
| Средняя длина (лемм) | — |
| Запросов с qrels | 15 |
| Среднее релевантных на запрос (grade≥2) | — |

## 5. Проверка коллекции (до сидирования)

1. JSON валиден, ext_id уникальны, категории из справочника §1.
2. Ни один заголовок не дублируется; text ≥ 150 слов.
3. По каждому запросу существует ≥ 4 документов с grade ≥ 2.
4. Межтематический «шум» присутствует (grep соседних терминов по чужим темам).
