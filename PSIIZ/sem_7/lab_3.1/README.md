# Lab 3.1 — In-Memory Secure Store

UI-приложение (Tkinter): CRUD данных **в оперативной памяти**.

## Запуск

```bash
cd lab_3.1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

В статус-баре показан **PID** процесса — его используй для дампов памяти.

## Типы записей

| Тип | Что в RAM |
|-----|-----------|
| `public` | открытый текст |
| `confidential_hash` | PBKDF2-HMAC-SHA256 (необратимо) |
| `confidential_enc` | Fernet/AES ciphertext (можно «Показать / расшифровать») |

## Дампы (п.4 задания)

В UI: кнопка **«Дамп RAM (make_dump.sh)»** → метка `after_create` / `after_update` / `after_delete`.

Или вручную:

```bash
./make_dump.sh <PID> after_create
```

Артефакты в `dumps/<label>_pid…/`:`meta.txt`, `store_snapshot.txt`, `vmmap.txt`/`maps.txt`, при удаче — `core` + `strings_head.txt`.

На macOS полный `core` часто требует прав отладчика (`DevToolsSecurity` / sudo). Для отчёта хватает snapshot + vmmap + поиск строк.
