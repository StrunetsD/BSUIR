# Lab 2.1 — VulnNotes

Намеренно уязвимое веб-приложение (**Flask + SQLite**) в контейнере **Ubuntu 22.04**.

Карта уязвимостей — по **OWASP Top 10:2025**  
https://owasp.org/Top10/2025/

> **Не использовать в production.**

---

## Быстрый старт

```bash
cd lab_2.1
docker compose --env-file /dev/null up -d --build
# UI: http://localhost:5050
# Карта: http://localhost:5050/vulns
```

| Логин | Пароль | Роль |
|-------|--------|------|
| `admin` | `admin` | admin |
| `alice` | `alice` | user |
| `bob` | `bob123` | user |
| `guest` | `guest` | guest |

```bash
docker exec -it -u appuser psiiz-vulnnotes bash   # shell в Ubuntu
docker compose --env-file /dev/null down -v       # стоп
```

---

## Функционал (задание 2.1)

| Функция | Эндпоинт |
|---------|----------|
| Регистрация | `/register` |
| Логин / logout | `/login`, `/logout` |
| CRUD публичных | `/public` … |
| CRUD конфиденциальных | `/confidential` … |
| Поиск | `/search?q=` |

---

## OWASP Top 10:2025 — все уязвимости в приложении

### A01:2025 — Broken Access Control

*(в 2025 сюда же относят SSRF, раньше отдельный A10:2021)*

| Место | Что сломано |
|-------|-------------|
| `GET /confidential/<id>` | IDOR — чтение чужих секретов |
| edit/delete confidential & public | нет проверки владельца |
| `GET /api/notes/<id>` | API без авторизации |
| `POST /fetch` | **SSRF** — сервер ходит по любому URL |

**Демо**

```bash
# IDOR: войти как alice → открыть /confidential/1

curl http://localhost:5050/api/notes/1

# SSRF (нужна сессия): /fetch → http://127.0.0.1:5000/debug/config
```

---

### A02:2025 — Security Misconfiguration

| Место | Что сломано |
|-------|-------------|
| `DEBUG=True` | debug Flask «в проде» |
| `secret_key` в коде | хардкод секрета |
| `GET /debug/config` | открытый debug endpoint |
| `0.0.0.0:5000` | слушает все интерфейсы |
| cookie без Secure | сессия по HTTP |

**Демо:** `curl http://localhost:5050/debug/config`

---

### A03:2025 — Software Supply Chain Failures

*(расширение старого «Vulnerable Components»)*

| Место | Что сломано |
|-------|-------------|
| `requirements.txt` | Flask `2.3.3` / Werkzeug `2.3.7` без hash-pinning |
| нет SBOM / audit | зависимости не проверяются |
| `pip install` в Docker от root | нет изоляции/подписи артефактов |
| использование `pickle` | небезопасный формат из «цепочки» данных |

**Демо**

```bash
docker exec psiiz-vulnnotes pip3 show flask werkzeug
cat requirements.txt
# нет --require-hashes, нет lockfile с подписью
```

---

### A04:2025 — Cryptographic Failures

| Место | Что сломано |
|-------|-------------|
| `users.password` | plaintext в SQLite |
| нет TLS | логин/пароль по HTTP |
| `confidential_notes` | PII без at-rest encryption |

**Демо**

```bash
docker exec -u appuser psiiz-vulnnotes python3 -c \
  "import sqlite3;print(list(sqlite3.connect('/app/data/app.db').execute('select username,password from users')))"
```

---

### A05:2025 — Injection

| Место | Тип |
|-------|-----|
| `POST /login` | SQL Injection |
| `GET /search?q=` | SQL Injection |
| `GET /search?q=` | Reflected XSS |

**Демо**

```text
Login username:  ' OR '1'='1' --
Search XSS:      /search?q=<script>alert(1)</script>
```

---

### A06:2025 — Insecure Design

| Проблема | Проявление |
|----------|------------|
| Нет rate limit | brute force login |
| Нет MFA / lockout | только слабый пароль |
| Нет политики паролей | `a` проходит register |
| Модель доступа | confidential без owner-check by design |

---

### A07:2025 — Authentication Failures

| Место | Что сломано |
|-------|-------------|
| сид-пароли | `admin`, `alice`, `guest` |
| `SESSION_COOKIE_HTTPONLY = False` | cookie читается JS |
| нет lockout | бесконечные попытки входа |

**Демо:** DevTools → Cookies → `session` без HttpOnly; XSS (A05) может украсть сессию.

---

### A08:2025 — Software or Data Integrity Failures

| Место | Что сломано |
|-------|-------------|
| `POST /import` | `pickle.loads()` от пользователя |

**Демо:** http://localhost:5050/import — hex pickle payload (на странице есть sample).

---

### A09:2025 — Security Logging and Alerting Failures

| Событие | Лог / алерт |
|---------|-------------|
| Failed login | **нет** |
| IDOR / mass access | **нет** |
| Brute force | **нет** алертов |
| Доступ к `/debug/config` | **нет** |

**Демо:** неверные пароли на `/login` → в `docker logs` нет security-событий.

---

### A10:2025 — Mishandling of Exceptional Conditions

*(новая категория: ошибки, fail-open, утечки при исключениях)*

| Место | Что сломано |
|-------|-------------|
| `/search` при битом SQL | в ответ уходит **SQL + exception text** |
| `DEBUG=True` | подробные traceback'и Werkzeug |
| `/fetch` при ошибке | сырой exception клиенту |
| `/import` при плохом pickle | детали ошибки наружу |
| нет единого error handler | непредсказуемое поведение при сбоях |

**Демо**

```text
/search?q='
→ страница с "SQL error: ..." и текстом запроса
```

---

## Сводная таблица (2025)

| ID | Категория | Где в VulnNotes |
|----|-----------|-----------------|
| **A01** | Broken Access Control | IDOR, unauth API, **SSRF `/fetch`** |
| **A02** | Security Misconfiguration | DEBUG, `/debug/config`, hardcode secret |
| **A03** | Software Supply Chain Failures | старые deps без hashes / SBOM |
| **A04** | Cryptographic Failures | plaintext passwords, no TLS |
| **A05** | Injection | SQLi login/search, XSS search |
| **A06** | Insecure Design | no rate limit / MFA / password policy |
| **A07** | Authentication Failures | weak passwords, no HttpOnly |
| **A08** | Software or Data Integrity Failures | `/import` pickle |
| **A09** | Security Logging and Alerting Failures | no failed-login logs/alerts |
| **A10** | Mishandling of Exceptional Conditions | verbose SQL/debug errors |

### Что изменилось относительно Top 10:2021

| 2021 | 2025 |
|------|------|
| A10 SSRF | вошёл в **A01** |
| A06 Vulnerable Components | расширен → **A03 Supply Chain** |
| — | новый **A10 Exceptional Conditions** |
| Misconfiguration был #5 | теперь **A02** (#2) |

---

## Privilege Escalation (Ubuntu, lab 2.2)

Процесс Flask = `appuser`. После shell:

| Вектор | Команда |
|--------|---------|
| SUID | `/usr/local/bin/backup-tool -p -c id` → `uid=0` |
| sudo find | `sudo find /tmp -exec /bin/sh -p \; -quit` |
| secrets on disk | `/opt/backup/.root_hint`, `~/.env` |

Это root **внутри контейнера**, не на хосте Mac.

---

## Структура

```
lab_2.1/
├── app.py
├── Dockerfile          # Ubuntu 22.04 + appuser + privesc
├── docker-compose.yml
├── requirements.txt
├── README.md           # этот файл (OWASP 2025)
├── OWASP.md            # краткая карта
└── 2.1.pdf
```

---

## Для отчёта 2.1

Пиши: приложение **не защищено**. Разбор по A01–A10:2025 + пункты задания (ОС / компоненты / сеть / конфиденциальность).
