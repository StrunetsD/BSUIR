#!/bin/bash
set -euo pipefail

USER_NAME="${SSH_USER:-labuser}"
USER_PASS="${SSH_PASSWORD:-LabUserPass123!}"

if ! id "$USER_NAME" &>/dev/null; then
  useradd -m -s /bin/bash "$USER_NAME"
  echo "${USER_NAME}:${USER_PASS}" | chpasswd
fi

mkdir -p /var/log/nginx
touch /var/log/nginx/access.log /var/log/nginx/error.log /var/log/auth.log
chmod 666 /var/log/auth.log /var/log/nginx/access.log || true

cat >/etc/rsyslog.conf <<'EOF'
module(load="imuxsock")
$FileOwner root
$FileGroup adm
$FileCreateMode 0644
auth,authpriv.*    /var/log/auth.log
*.*;auth,authpriv.none  -/var/log/syslog
EOF

rsyslogd
sleep 0.5

grep -q '^SyslogFacility' /etc/ssh/sshd_config || echo 'SyslogFacility AUTH' >> /etc/ssh/sshd_config
grep -q '^LogLevel' /etc/ssh/sshd_config || echo 'LogLevel VERBOSE' >> /etc/ssh/sshd_config

/usr/sbin/sshd
echo "$(date -u '+%b %e %H:%M:%S') lab41-server sshd[$$]: Server listening on 0.0.0.0 port 22." >> /var/log/auth.log

nginx -g 'daemon off;'
