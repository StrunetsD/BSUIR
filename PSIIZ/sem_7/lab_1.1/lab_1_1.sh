#!/usr/bin/env bash
# Лабораторная работа №1.1
# Управление доступом к объектам ОС (традиционные права Unix / ACL-модель u-g-o)
# Требуется: Linux, запуск от root (sudo ./lab_1_1.sh)

set -u

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${WORK_DIR:-$BASE_DIR/pzs}"
LOG_FILE="${LOG_FILE:-$BASE_DIR/lab_1_1_results.log}"
PASSWD_DUMMY="Passw0rd!"

USERS=(iit11 iit12 iit21 iit22 iit3)
GROUPS=(group_iit1 group_iit2)
FOLDERS=(pzs11 pzs12 pzs13 pzs14)
TEST_USERS=(iit11 iit12 iit21 iit22 iit3 root)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
  local msg="$*"
  echo -e "$msg" | tee -a "$LOG_FILE"
}

ok()   { log "${GREEN}[OK]${NC} $*"; }
fail() { log "${RED}[FAIL]${NC} $*"; }
info() { log "${YELLOW}[INFO]${NC} $*"; }

require_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "Скрипт нужно запускать от root: sudo $0"
    exit 1
  fi
}

cleanup_previous() {
  info "Очистка предыдущих артефактов (если есть)..."
  for u in "${USERS[@]}"; do
    if id "$u" &>/dev/null; then
      pkill -9 -u "$u" 2>/dev/null || true
      userdel -r "$u" 2>/dev/null || userdel "$u" 2>/dev/null || true
    fi
  done
  for g in "${GROUPS[@]}" groupt_iit1; do
    getent group "$g" &>/dev/null && groupdel "$g" 2>/dev/null || true
  done
  rm -rf "$WORK_DIR"
}

create_groups_and_users() {
  info "1–5. Создание групп и пользователей..."

  groupadd group_iit1
  groupadd group_iit2
  ok "Группы group_iit1, group_iit2 созданы"

  useradd -m -s /bin/bash -G group_iit1 iit11
  useradd -m -s /bin/bash -G group_iit1 iit12
  useradd -m -s /bin/bash -G group_iit2 iit21
  useradd -m -s /bin/bash -G group_iit2 iit22
  useradd -m -s /bin/bash iit3

  for u in "${USERS[@]}"; do
    echo "$u:$PASSWD_DUMMY" | chpasswd
  done
  ok "Пользователи iit11, iit12, iit21, iit22, iit3 созданы"

  # 4. Административные привилегии для iit21
  if getent group sudo &>/dev/null; then
    usermod -aG sudo iit21
  elif getent group wheel &>/dev/null; then
    usermod -aG wheel iit21
  else
    groupadd sudo
    usermod -aG sudo iit21
  fi
  # passwordless sudo — чтобы проверки могли использовать привилегии
  echo 'iit21 ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/iit21
  chmod 440 /etc/sudoers.d/iit21
  ok "Пользователь iit21 добавлен в группу администраторов (sudo/wheel)"
}

create_directories() {
  info "6–11. Создание каталогов с заданными правами..."

  mkdir -p "$WORK_DIR"
  chmod 755 "$WORK_DIR"
  chown root:root "$WORK_DIR"

  # pzs11 — rwx только владельцу (iit11), чтобы он мог создавать файлы
  mkdir -p "$WORK_DIR/pzs11"
  chown iit11:iit11 "$WORK_DIR/pzs11"
  chmod 700 "$WORK_DIR/pzs11"
  ok "pzs11: 700, владелец iit11"

  # pzs12 — rwx только группе group_iit1
  mkdir -p "$WORK_DIR/pzs12"
  chown root:group_iit1 "$WORK_DIR/pzs12"
  chmod 070 "$WORK_DIR/pzs12"
  ok "pzs12: 070, группа group_iit1"

  # pzs13 — rwx только для остальных
  mkdir -p "$WORK_DIR/pzs13"
  chown root:root "$WORK_DIR/pzs13"
  chmod 007 "$WORK_DIR/pzs13"
  ok "pzs13: 007, только others"

  # pzs14 — rwx для всех
  mkdir -p "$WORK_DIR/pzs14"
  chown root:root "$WORK_DIR/pzs14"
  chmod 777 "$WORK_DIR/pzs14"
  ok "pzs14: 777, для всех"

  # pzs15 — rwx только для root
  mkdir -p "$WORK_DIR/pzs15"
  chown root:root "$WORK_DIR/pzs15"
  chmod 700 "$WORK_DIR/pzs15"
  ok "pzs15: 700, только root"
}

# Режим: owner | group | others | all | admin
# Права: r | rw | w | rwx | x
mode_for() {
  local who="$1" perms="$2"
  local bits=0
  case "$perms" in
    r)   bits=4 ;;
    rw)  bits=6 ;;
    w)   bits=2 ;;
    rwx) bits=7 ;;
    x)   bits=1 ;;
    *)   echo "Неизвестные права: $perms" >&2; return 1 ;;
  esac

  case "$who" in
    owner)  printf '%o' "$(( bits << 6 ))" ;;
    group)  printf '%o' "$(( bits << 3 ))" ;;
    others) printf '%o' "$bits" ;;
    all)    printf '%o' "$(( (bits << 6) | (bits << 3) | bits ))" ;;
    admin)  printf '%o' "$(( bits << 6 ))" ;;
    *)      echo "Неизвестный класс: $who" >&2; return 1 ;;
  esac
}

create_one_file() {
  local dir="$1" name="$2" who="$3" perms="$4"
  local path="$dir/$name"
  local mode tmp
  mode="$(mode_for "$who" "$perms")"
  tmp="$(mktemp)"

  if [[ "$name" =~ ^file[0-9]5$ ]]; then
    cat > "$tmp" <<'EOF'
#!/bin/bash
read testVariable
EOF
  else
    cat > "$tmp" <<'EOF'
#!/bin/bash
echo "Hello World"
EOF
  fi

  # П.12–13: файлы создаёт iit11 (копирование от его имени, если каталог доступен)
  if sudo -u iit11 cp "$tmp" "$path" 2>/dev/null; then
    :
  else
    cp "$tmp" "$path"
  fi
  rm -f "$tmp"

  if [[ "$who" == "admin" ]]; then
    chown root:root "$path"
  else
    chown iit11:group_iit1 "$path"
  fi
  chmod "$mode" "$path"
  ok "Создан $path (режим $mode, класс $who/$perms)"
}

create_files_in_dir() {
  local dir="$1"
  info "Создание файлов в $dir от пользователя iit11..."

  create_one_file "$dir" file11 owner  r
  create_one_file "$dir" file12 owner  rw
  create_one_file "$dir" file13 owner  w
  create_one_file "$dir" file14 owner  rwx
  create_one_file "$dir" file15 owner  x

  create_one_file "$dir" file21 group  r
  create_one_file "$dir" file22 group  rw
  create_one_file "$dir" file23 group  w
  create_one_file "$dir" file24 group  rwx
  create_one_file "$dir" file25 group  x

  create_one_file "$dir" file31 others r
  create_one_file "$dir" file32 others rw
  create_one_file "$dir" file33 others w
  create_one_file "$dir" file34 others rwx
  create_one_file "$dir" file35 others x

  create_one_file "$dir" file41 all    r
  create_one_file "$dir" file42 all    rw
  create_one_file "$dir" file43 all    w
  create_one_file "$dir" file44 all    rwx
  create_one_file "$dir" file45 all    x

  create_one_file "$dir" file51 admin  r
  create_one_file "$dir" file52 admin  rw
  create_one_file "$dir" file53 admin  w
  create_one_file "$dir" file54 admin  rwx
  create_one_file "$dir" file55 admin  x
}

can_read() {
  local user="$1" path="$2"
  if [[ "$user" == "root" ]]; then
    cat "$path" &>/dev/null
  else
    sudo -u "$user" cat "$path" &>/dev/null
  fi
}

can_write() {
  local user="$1" path="$2"
  if [[ "$user" == "root" ]]; then
    # не портим содержимое: дописываем и откатываем через временную метку
    printf '' >> "$path" 2>/dev/null
  else
    sudo -u "$user" bash -c "printf '' >> '$path'" &>/dev/null
  fi
}

can_exec() {
  local user="$1" path="$2"
  local runner
  if command -v timeout &>/dev/null; then
    runner=(timeout 1)
  else
    runner=()
  fi
  if [[ "$user" == "root" ]]; then
    "${runner[@]}" bash "$path" </dev/null &>/dev/null
  else
    "${runner[@]}" sudo -u "$user" bash "$path" </dev/null &>/dev/null
  fi
}

check_file_access() {
  info "14. Проверка чтения / записи / исполнения файлов..."

  local dir file user r w x
  for dir in "${FOLDERS[@]}"; do
    for file in "$WORK_DIR/$dir"/file*; do
      [[ -e "$file" ]] || continue
      for user in "${TEST_USERS[@]}"; do
        r=NO; w=NO; x=NO
        can_read  "$user" "$file" && r=YES
        can_write "$user" "$file" && w=YES
        can_exec  "$user" "$file" && x=YES
        log "FILE $(basename "$dir")/$(basename "$file") | user=$user | read=$r write=$w exec=$x"
      done
    done
  done
}

check_process_kill() {
  info "15. Запуск file*5 от iit11 и проверка возможности остановить процесс..."

  local dir file pid user killed
  for dir in "${FOLDERS[@]}"; do
    for file in "$WORK_DIR/$dir"/file{1,2,3,4,5}5; do
      [[ -e "$file" ]] || continue

      # запускаем в фоне от iit11; процесс будет ждать ввода на read
      sudo -u iit11 bash "$file" &>/dev/null &
      pid=$!
      sleep 0.3

      if ! kill -0 "$pid" 2>/dev/null; then
        log "PROC $(basename "$dir")/$(basename "$file") | не удалось запустить от iit11"
        continue
      fi

      for user in "${TEST_USERS[@]}"; do
        killed=NO
        if [[ "$user" == "root" ]]; then
          kill "$pid" 2>/dev/null && killed=YES
        elif [[ "$user" == "iit21" ]]; then
          if sudo -u "$user" kill "$pid" 2>/dev/null; then
            killed=YES
          elif sudo -u "$user" sudo kill "$pid" 2>/dev/null; then
            killed=YES
          fi
        else
          sudo -u "$user" kill "$pid" 2>/dev/null && killed=YES
        fi
        log "PROC $(basename "$dir")/$(basename "$file") pid=$pid | kill_by=$user | success=$killed"

        if [[ "$killed" == "YES" ]]; then
          wait "$pid" 2>/dev/null || true
          # перезапуск для следующей проверки, кроме последнего пользователя
          if [[ "$user" != "root" ]]; then
            sudo -u iit11 bash "$file" &>/dev/null &
            pid=$!
            sleep 0.3
          fi
        fi
      done

      kill -9 "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    done
  done
}

check_dir_ops() {
  info "16. Проверка операций с каталогами (list / create / delete)..."

  local dir user list create delete tmp victim
  for dir in pzs11 pzs12 pzs13 pzs14 pzs15; do
    for user in "${TEST_USERS[@]}"; do
      list=NO; create=NO; delete=NO

      if [[ "$user" == "root" ]]; then
        ls "$WORK_DIR/$dir" &>/dev/null && list=YES
        tmp="$WORK_DIR/$dir/.tmp_create_root_$$"
        if touch "$tmp" 2>/dev/null; then
          create=YES
          rm -f "$tmp"
        fi
        victim="$WORK_DIR/$dir/file11"
        if [[ -e "$victim" ]]; then
          # проверяем право на удаление без фактического удаления всех файлов:
          # пробуем unlink тестовой копии
          local probe="$WORK_DIR/$dir/.probe_del_$$"
          cp -a "$victim" "$probe" 2>/dev/null || touch "$probe" 2>/dev/null || true
          if [[ -e "$probe" ]] && rm -f "$probe" 2>/dev/null; then
            delete=YES
          fi
        else
          # в pzs15 файлов нет — проверяем удаление созданного probe
          local probe="$WORK_DIR/$dir/.probe_del_$$"
          if touch "$probe" 2>/dev/null && rm -f "$probe" 2>/dev/null; then
            delete=YES
          fi
        fi
      else
        sudo -u "$user" ls "$WORK_DIR/$dir" &>/dev/null && list=YES
        tmp="$WORK_DIR/$dir/.tmp_create_${user}_$$"
        if sudo -u "$user" touch "$tmp" 2>/dev/null; then
          create=YES
          sudo -u "$user" rm -f "$tmp" 2>/dev/null || rm -f "$tmp"
        fi
        local probe="$WORK_DIR/$dir/.probe_del_${user}_$$"
        # probe создаём от root (чтобы объект существовал), удаление — от user
        if [[ "$create" == "YES" ]] || touch "$probe" 2>/dev/null; then
          chown "$user":"$user" "$probe" 2>/dev/null || true
          if sudo -u "$user" rm -f "$probe" 2>/dev/null; then
            delete=YES
          else
            # если не смогли удалить «чужой»/свой probe — фиксируем NO
            rm -f "$probe" 2>/dev/null || true
          fi
        fi
      fi

      log "DIR $dir | user=$user | list=$list create=$create delete=$delete"
    done
  done
}

final_cleanup() {
  info "17. Удаление созданных файлов, каталогов, пользователей и групп..."

  pkill -9 -u iit11 2>/dev/null || true
  pkill -9 -u iit12 2>/dev/null || true
  pkill -9 -u iit21 2>/dev/null || true
  pkill -9 -u iit22 2>/dev/null || true
  pkill -9 -u iit3  2>/dev/null || true

  rm -rf "$WORK_DIR"
  ok "Каталог $WORK_DIR удалён"

  for u in iit11 iit12 iit21 iit22 iit3; do
    userdel -r "$u" 2>/dev/null || userdel "$u" 2>/dev/null || true
    ok "Пользователь $u удалён"
  done
  rm -f /etc/sudoers.d/iit21

  # в задании опечатка groupt_iit1 — удаляем обе формы на всякий случай
  for g in group_iit1 groupt_iit1 group_iit2; do
    getent group "$g" &>/dev/null && groupdel "$g" && ok "Группа $g удалена" || true
  done
}

show_summary() {
  info "Текущее состояние перед проверками:"
  log "--- groups ---"
  getent group group_iit1 group_iit2 | tee -a "$LOG_FILE"
  log "--- users ---"
  getent passwd iit11 iit12 iit21 iit22 iit3 | tee -a "$LOG_FILE"
  log "--- tree ---"
  ls -laR "$WORK_DIR" | tee -a "$LOG_FILE"
}

main() {
  require_root
  : > "$LOG_FILE"
  log "=== Лабораторная 1.1 | $(date) ==="
  log "WORK_DIR=$WORK_DIR"
  log "Результаты также пишутся в $LOG_FILE"

  cleanup_previous
  create_groups_and_users
  create_directories

  info "12–13. Создание файлов от пользователя iit11..."
  for d in "${FOLDERS[@]}"; do
    create_files_in_dir "$WORK_DIR/$d"
  done

  show_summary
  check_file_access
  check_process_kill
  check_dir_ops

  if [[ "${KEEP_ENV:-0}" == "1" ]]; then
    info "KEEP_ENV=1 — очистка пропущена. Для удаления: KEEP_ENV=0 sudo $0 --cleanup-only"
  else
    final_cleanup
  fi

  log "=== Готово. Лог: $LOG_FILE ==="
}

cleanup_only() {
  require_root
  final_cleanup
}

case "${1:-}" in
  --cleanup-only) cleanup_only ;;
  *) main "$@" ;;
esac
