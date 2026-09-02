# Lab 4.2 — Suricata IDS на стенде nginx+SSH

Вариант из задания: **Suricata**.  
Стенд: тот же сервер, что в 4.1 (сборка из `lab_4.1/server`), порты **8081** / **2223**.

## Запуск

```bash
cd lab_4.2
touch logs/auth.log
mkdir -p logs/nginx logs/suricata logs/before logs/after

docker compose --env-file /dev/null up -d --build
# страница: http://localhost:8081
# SSH: ssh -p 2223 labuser@localhost  /  LabUserPass123!
```

## Сценарий до / после

```bash
chmod +x scripts/*.sh

# 1) обычный трафик + снимок без опоры на алерты IDS
docker run --rm --network lab_42_default curlimages/curl:8.5.0 -sS -o /dev/null http://server/
./scripts/snapshot_before.sh

# 2) атаки (из Docker-сети — надёжно видно Suricata на eth0)
./scripts/gen_attacks.sh

# 3) алерты + демо IPS (deny-list)
sleep 3
./scripts/analyze_suricata.sh
./scripts/ips_response_demo.sh

ls logs/suricata/   # fast.log  eve.json  suricata.log
```

## Отчёт

```bash
source ../lab_3.1/.venv/bin/activate   # или venv с fpdf2+pillow
python3 report/make_shots.py
python3 report/generate_report.py
# → Отчет_ЛР4.2_Струнец_ДП_321701.pdf
```

## Остановка

```bash
docker compose --env-file /dev/null down -v
```
