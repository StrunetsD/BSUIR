#!/usr/bin/env bash
# Большой учебный архив логов «за несколько дней» (nginx + SSH).
# DAYS=14 (по умолчанию) — сколько суток назад симулировать.
set -euo pipefail
C="${CONTAINER:-psiiz-lab41-server}"
DAYS="${DAYS:-14}"

docker exec -e DAYS="$DAYS" "$C" bash -c '
ACCESS=/var/log/nginx/access.log
AUTH=/var/log/auth.log
touch "$ACCESS" "$AUTH"

UAS=(
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605.1.15"
  "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0"
  "curl/8.0.1"
  "python-requests/2.31.0"
  "sqlmap/1.7.2#stable"
  "zgrab/0.x"
  "masscan/1.3"
)

GOOD_PATHS=("/" "/health" "/" "/favicon.ico" "/")
PROBE_PATHS=("/admin" "/wp-login.php" "/.env" "/phpmyadmin" "/server-status" "/actuator" "/.git/config" "/xmlrpc.php" "/api/v1/users" "/cgi-bin/luci")

GOOD_IPS=("203.0.113.10" "203.0.113.20" "198.51.100.5" "192.0.2.40")
BAD_IPS=("198.51.100.77" "203.0.113.200" "192.0.2.222" "198.51.100.13" "203.0.113.99")

n_access=0
n_auth=0

for ((day=DAYS-1; day>=0; day--)); do
  ds=$(date -u -d "-${day} day" "+%d/%b/%Y")
  ts_base=$(date -u -d "-${day} day" "+%b %e")

  # нормальный трафик: ~40–80 запросов/день
  good_n=$((40 + RANDOM % 41))
  for ((i=0; i<good_n; i++)); do
    ip=${GOOD_IPS[$((RANDOM % ${#GOOD_IPS[@]}))]}
    path=${GOOD_PATHS[$((RANDOM % ${#GOOD_PATHS[@]}))]}
    ua=${UAS[$((RANDOM % 4))]}
    hh=$(printf "%02d" $((RANDOM % 24)))
    mm=$(printf "%02d" $((RANDOM % 60)))
    ss=$(printf "%02d" $((RANDOM % 60)))
    code=200
    [[ "$path" == "/favicon.ico" ]] && code=404
    size=$((200 + RANDOM % 800))
    echo "$ip - - [${ds}:${hh}:${mm}:${ss} +0000] \"GET ${path} HTTP/1.1\" ${code} ${size} \"-\" \"${ua}\"" >> "$ACCESS"
    n_access=$((n_access+1))
  done

  # сканы / пробы: ~25–60/день
  bad_n=$((25 + RANDOM % 36))
  for ((i=0; i<bad_n; i++)); do
    ip=${BAD_IPS[$((RANDOM % ${#BAD_IPS[@]}))]}
    path=${PROBE_PATHS[$((RANDOM % ${#PROBE_PATHS[@]}))]}
    # иногда рандомный unknown
    if (( RANDOM % 5 == 0 )); then
      path="/unknown$((RANDOM % 500))"
    fi
    ua=${UAS[$((4 + RANDOM % 4))]}
    hh=$(printf "%02d" $((3 + RANDOM % 4)))   # чаще ночью
    mm=$(printf "%02d" $((RANDOM % 60)))
    ss=$(printf "%02d" $((RANDOM % 60)))
    echo "$ip - - [${ds}:${hh}:${mm}:${ss} +0000] \"GET ${path} HTTP/1.1\" 404 162 \"-\" \"${ua}\"" >> "$ACCESS"
    n_access=$((n_access+1))
  done

  # SSH брутфорс: ~15–40 fail/день с разных IP
  ssh_n=$((15 + RANDOM % 26))
  for ((i=0; i<ssh_n; i++)); do
    ip=${BAD_IPS[$((RANDOM % ${#BAD_IPS[@]}))]}
    hh=$(printf "%02d" $((RANDOM % 24)))
    mm=$(printf "%02d" $((RANDOM % 60)))
    ss=$(printf "%02d" $((RANDOM % 60)))
    port=$((40000 + RANDOM % 20000))
    pid=$((200 + RANDOM % 5000))
    case $((RANDOM % 4)) in
      0) echo "${ts_base} ${hh}:${mm}:${ss} lab41-server sshd[${pid}]: Failed password for invalid user admin from ${ip} port ${port} ssh2" >> "$AUTH" ;;
      1) echo "${ts_base} ${hh}:${mm}:${ss} lab41-server sshd[${pid}]: Failed password for invalid user root from ${ip} port ${port} ssh2" >> "$AUTH" ;;
      2) echo "${ts_base} ${hh}:${mm}:${ss} lab41-server sshd[${pid}]: Failed password for labuser from ${ip} port ${port} ssh2" >> "$AUTH" ;;
      3) echo "${ts_base} ${hh}:${mm}:${ss} lab41-server sshd[${pid}]: Invalid user ubuntu from ${ip} port ${port}" >> "$AUTH" ;;
    esac
    n_auth=$((n_auth+1))
  done

  # пара успешных входов labuser (легитим)
  for ((i=0; i<2; i++)); do
    ip=${GOOD_IPS[$((RANDOM % ${#GOOD_IPS[@]}))]}
    hh=$(printf "%02d" $((9 + RANDOM % 8)))
    mm=$(printf "%02d" $((RANDOM % 60)))
    ss=$(printf "%02d" $((RANDOM % 60)))
    port=$((50000 + RANDOM % 10000))
    pid=$((6000 + RANDOM % 2000))
    echo "${ts_base} ${hh}:${mm}:${ss} lab41-server sshd[${pid}]: Accepted password for labuser from ${ip} port ${port} ssh2" >> "$AUTH"
    n_auth=$((n_auth+1))
  done
done

echo "Seeded DAYS=${DAYS}: access+=${n_access} auth+=${n_auth}"
'
