FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    DB_PATH=/app/data/app.db

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        curl \
        ca-certificates \
        sudo \
        net-tools \
        iproute2 \
        procps \
        vim-tiny \
    && rm -rf /var/lib/apt/lists/*

# Непривилегированный пользователь приложения (цель RCE → потом privesc)
RUN useradd -m -s /bin/bash appuser \
    && mkdir -p /app/data /opt/backup /var/backups/vulnnotes \
    && chown -R appuser:appuser /app /home/appuser

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app.py .
COPY entrypoint.sh /entrypoint.sh

# --- намеренные misconfig для локального privilege escalation (lab 2.2) ---
# 1) sudo без пароля на опасную утилиту
RUN echo 'appuser ALL=(ALL) NOPASSWD: /usr/bin/find' > /etc/sudoers.d/appuser \
    && chmod 440 /etc/sudoers.d/appuser

# 2) SUID binary — учебный вектор privesc
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev linux-libc-dev \
    && echo '#include <unistd.h>' > /tmp/rootshell.c \
    && echo 'int main(int argc, char **argv){ setuid(0); setgid(0); if(argc>1) execv("/bin/bash", argv); execl("/bin/bash","bash","-p",(char*)0); return 0; }' >> /tmp/rootshell.c \
    && gcc /tmp/rootshell.c -o /usr/local/bin/backup-tool \
    && chown root:root /usr/local/bin/backup-tool \
    && chmod 4755 /usr/local/bin/backup-tool \
    && rm -f /tmp/rootshell.c \
    && apt-get purge -y gcc libc6-dev linux-libc-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# 3) world-writable cron-like backup dir + root-owned script вызываемый из entrypoint watch (упрощённо: файл с root credentials)
RUN echo 'root:LabRootPass123!' > /opt/backup/.root_hint \
    && chmod 644 /opt/backup/.root_hint \
    && echo 'PATH=/usr/local/bin:/usr/bin' > /home/appuser/.bashrc \
    && chown appuser:appuser /home/appuser/.bashrc

# 4) запись в /etc/passwd через soft link target в /tmp (классика) — writable /etc/shadow? нет, слишком жёстко
#    вместо этого: конфиг с паролем postgres-style в home
RUN echo 'DB_ADMIN_PASSWORD=LabRootPass123!' > /home/appuser/.env \
    && chown appuser:appuser /home/appuser/.env \
    && chmod 644 /home/appuser/.env

RUN chmod +x /entrypoint.sh \
    && chown appuser:appuser /app/app.py

USER appuser
EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]
