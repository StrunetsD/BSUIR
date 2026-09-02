# Lab 4.1 — анализ запросов (Docker-стенд)

Учебный «удалённый сервер»: **nginx + OpenSSH** в одном контейнере.  
Трафик и «атаки» генерируются локально (не публикуем порт в Internet).

## Быстрый старт

```bash
cd lab_4.1
docker compose --env-file /dev/null up -d --build

# страница
open http://localhost:8080
# SSH
ssh -p 2222 labuser@localhost
# пароль: LabUserPass123!
```

## Трафик и логи

```bash
chmod +x scripts/*.sh

# много «исторических» логов (~14 суток)
DAYS=14 ./scripts/seed_history.sh

# живой трафик (плотный)
WEB_ROUNDS=40 SSH_ROUNDS=25 ./scripts/gen_traffic.sh

./scripts/analyze_logs.sh
```

Повтори `seed_history` / `gen_traffic`, если нужно ещё больше строк.

## Порты

| Сервис | Хост |
|--------|------|
| HTTP | http://localhost:8080 |
| SSH | localhost:2222 (`labuser` / `LabUserPass123!`) |

## Что смотреть в отчёте

- `access.log` — IP, URI, статус, User-Agent (пробы `/admin`, sqlmap, 404).
- `auth.log` — Failed password, invalid user, запрет root.
- Рекомендации: ключи вместо пароля, fail2ban, `PermitRootLogin no` (уже), firewall, IDS (→ lab 4.2).

```bash
docker compose --env-file /dev/null down -v
```
