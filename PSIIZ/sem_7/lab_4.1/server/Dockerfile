FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx \
        openssh-server \
        rsyslog \
        sudo \
        ca-certificates \
        openssl \
        iproute2 \
        net-tools \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/run/sshd /var/log/nginx \
    && touch /var/log/auth.log \
    && chmod 640 /var/log/auth.log

COPY nginx/default.conf /etc/nginx/sites-available/default
RUN rm -f /etc/nginx/sites-enabled/default \
    && ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

RUN sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config \
    && grep -q '^AllowUsers' /etc/ssh/sshd_config || echo 'AllowUsers labuser' >> /etc/ssh/sshd_config \
    && ssh-keygen -A \
    && printf '%s\n' \
        'auth,authpriv.*                 /var/log/auth.log' \
        '*.*;auth,authpriv.none          -/var/log/syslog' \
        > /etc/rsyslog.d/50-default-lab.conf

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22 80
CMD ["/entrypoint.sh"]
