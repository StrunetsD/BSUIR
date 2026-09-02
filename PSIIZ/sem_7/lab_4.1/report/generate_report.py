#!/usr/bin/env python3
"""Отчёт lab 4.1 — анализ запросов SSH и веб-сервера."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
OUT = ROOT / "Отчет_ЛР4.1_Струнец_ДП_321701.pdf"

FONT = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"


class Report(FPDF):
    def __init__(self) -> None:
        super().__init__(format="A4", unit="mm")
        self.set_auto_page_break(auto=True, margin=20)
        self.add_font("TimesNR", "", FONT)
        self.add_font("TimesNR", "B", FONT_B)
        self.fig = 0

    def footer(self) -> None:
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("TimesNR", "", 12)
        self.cell(0, 8, str(self.page_no()), align="R")

    def body(self, size: float = 14) -> None:
        self.set_font("TimesNR", "", size)

    def bold(self, size: float = 14) -> None:
        self.set_font("TimesNR", "B", size)

    def para(self, text: str) -> None:
        self.body(14)
        self.multi_cell(
            self.epw, 7.5, " " * 8 + text, align="J",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        self.ln(1)

    def h1(self, text: str) -> None:
        self.ln(3)
        self.bold(14)
        self.multi_cell(0, 8, text.upper(), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def h2(self, text: str) -> None:
        self.ln(2)
        self.bold(14)
        self.multi_cell(0, 7.5, text, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def bullet(self, text: str) -> None:
        self.body(14)
        self.set_x(self.l_margin + 8)
        self.multi_cell(
            self.epw - 8, 7.5, "– " + text, align="J",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )

    def caption(self, title: str) -> None:
        self.fig += 1
        self.body(12)
        self.multi_cell(
            0, 6, f"Рисунок {self.fig} – {title}", align="C",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        self.ln(2)

    def shot(self, name: str, title: str, max_h: float = 95) -> None:
        path = SHOTS / name
        if not path.exists():
            return
        if self.get_y() + max_h + 18 > self.h - self.b_margin:
            self.add_page()
        self.image(str(path), x=self.l_margin, w=self.epw, h=max_h, keep_aspect_ratio=True)
        self.ln(2)
        self.caption(title)


def title_page(pdf: Report) -> None:
    pdf.add_page()
    pdf.set_margins(30, 20, 15)
    pdf.bold(14)
    for line in (
        "Министерство образования Республики Беларусь",
        "Учреждение образования",
        "«Белорусский государственный университет",
        "информатики и радиоэлектроники»",
        "",
        "Факультет информационных технологий и управления",
        "Кафедра интеллектуальных информационных технологий",
    ):
        pdf.multi_cell(0, 7, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(24)
    for line in (
        "ОТЧЁТ",
        "по лабораторной работе № 4 (часть 1)",
        "по дисциплине",
        "«Проектирование защищенных интеллектуальных",
        "информационных систем»",
    ):
        pdf.multi_cell(0, 7.5, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.body(14)
    pdf.multi_cell(
        0, 7.5,
        "Тема: Анализ запросов из сети (SSH и веб-сервер)",
        align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(32)
    pdf.set_xy(105, pdf.get_y())
    pdf.multi_cell(
        80, 7.5,
        "Выполнил:\nстудент группы 321701\nСтрунец Д. П.\n\nПроверил:\nСальников Д. А.",
        align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_y(-35)
    pdf.multi_cell(0, 7.5, "Минск 2026", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def build() -> Path:
    pdf = Report()
    pdf.set_margins(30, 20, 15)
    title_page(pdf)

    pdf.add_page()
    pdf.h1("1 Постановка задачи")
    pdf.para(
        "Целью работы является развёртывание веб-сервера с тестовой страницей, "
        "настройка журналирования и анализ логов SSH и HTTP за несколько суток "
        "для выявления легитимной активности и признаков атак (сканирование, "
        "подбор пароля)."
    )
    pdf.para(
        "Стенд реализован в Docker (Ubuntu 22.04): nginx + OpenSSH в одном "
        "контейнере. Порты хоста: HTTP — 8080, SSH — 2222. Трафик учебный "
        "(генераторы seed_history.sh / gen_traffic.sh), без публикации сервисов "
        "в публичный Internet."
    )

    pdf.h1("2 Краткое описание веб-сервера")
    pdf.para(
        "Используется nginx (пакет Ubuntu). Документный корень — /var/www/html, "
        "тестовая страница index.html (Lab 4.1). Формат журнала access — combined "
        "(IP, время, метод, URI, код ответа, User-Agent). error_log — уровень warn. "
        "Проверка доступности: GET / и /health возвращают HTTP 200."
    )
    pdf.shot("05_compose.png", "Схема docker-compose стенда", 70)
    pdf.shot("04_web_page.png", "Ответ тестовой страницы (фрагмент HTML)", 80)

    pdf.h1("3 Описание анализируемых файлов")
    pdf.h2("3.1 /var/log/nginx/access.log")
    pdf.para(
        "Журнал HTTP-запросов. Нужен для анализа популярных URI, кодов ответа, "
        "источников (IP) и User-Agent. На хосте файл смонтирован в "
        "lab_4.1/logs/nginx/access.log."
    )
    pdf.h2("3.2 /var/log/auth.log")
    pdf.para(
        "Журнал аутентификации (sshd через rsyslog). Содержит Failed password, "
        "Invalid user, Accepted password, listening. Используется для выявления "
        "брутфорса SSH и успешных входов. На хосте — lab_4.1/logs/auth.log."
    )
    pdf.h2("3.3 Вспомогательные артефакты")
    for t in (
        "scripts/seed_history.sh — ретроспектива за DAYS суток;",
        "scripts/gen_traffic.sh — живой трафик и неудачные SSH;",
        "scripts/analyze_logs.sh — сводка top paths / status / Failed.",
    ):
        pdf.bullet(t)

    pdf.h1("4 Анализ запросов из сети")
    pdf.h2("4.1 Веб-сервер (nginx)")
    pdf.para(
        "Объём выборки: около 3400 записей access.log за период примерно с "
        "20.08.2026 по 02.09.2026. Легитимные запросы: GET / и /health "
        "(суммарно порядка 1500 успешных 200). Одновременно зафиксировано "
        "около 1900 ответов 404 — преимущественно сканирование."
    )
    pdf.para("Типичные признаки атаки в access.log:")
    for t in (
        "URI: /admin, /wp-login.php, /.env, /phpmyadmin, /.git/config, /xmlrpc.php;",
        "User-Agent: sqlmap, zgrab, masscan, python-requests;",
        "источники из учебных диапазонов документации (198.51.100.0/24, 203.0.113.0/24) и адрес генератора на хосте.",
    ):
        pdf.bullet(t)
    pdf.shot("01_analysis.png", "Сводка по access.log и auth.log", 110)
    pdf.shot("02_access_tail.png", "Фрагмент access.log", 90)

    pdf.h2("4.2 SSH-сервер")
    pdf.para(
        "В auth.log ≈ 1100 строк. Зафиксировано порядка 650 Failed password, "
        "≈ 180 Invalid user (root/admin/ubuntu и др.) и около 50 Accepted password "
        "для учётной записи labuser (легитимные входы). PermitRootLogin no и "
        "AllowUsers labuser ограничивают вход root; попытки root отражаются как "
        "invalid user / отказ."
    )
    pdf.para(
        "Паттерн брутфорса: серии Failed password с одних и тех же IP "
        "(например 198.51.100.77, 203.0.113.99) в разные сутки — типичный "
        "перебор по словарю."
    )
    pdf.shot("03_auth_sample.png", "Фрагмент auth.log (Failed / Accepted)", 95)

    pdf.h1("5 Рекомендации по улучшению безопасности")
    for t in (
        "Отключить парольную аутентификацию SSH, оставить только ключи; сложный пароль, если пароль неизбежен.",
        "fail2ban / sshguard по auth.log; лимит MaxAuthTries, смена порта только как доп. мера.",
        "Firewall (ufw/nftables): SSH только с доверенных IP; веб — 80/443.",
        "Для nginx: скрыть версию, rate limit, запрет чувствительных URI, TLS (HTTPS).",
        "Централизованный сбор логов и IDS/IPS (Suricata/Snort — лабораторная работа № 4.2).",
        "Регулярный аудит access.log/auth.log; ротация логов (logrotate).",
        "Не публиковать учебный стенд с паролем LabUserPass123! в Internet.",
    ):
        pdf.bullet(t)

    pdf.h1("6 Вывод")
    pdf.para(
        "Семантическая составляющая. Развёрнут журналируемый стенд nginx+SSH; "
        "по логам за несколько суток отделены легитимные запросы от сканирования "
        "веб-приложения и SSH-брутфорса; показана роль access.log и auth.log."
    )
    pdf.para(
        "Прагматическая составляющая. Получен воспроизводимый Docker-стенд и "
        "скрипты генерации/разбора трафика; сформулированы практические меры "
        "усиления защиты удалённого сервера, развиваемые в части 2 (IDS/IPS)."
    )

    pdf.h1("Список использованных источников")
    for i, s in enumerate(
        [
            "Документация nginx: ngx_http_log_module [Электронный ресурс]. – https://nginx.org/en/docs/http/ngx_http_log_module.html",
            "OpenSSH: sshd_config [Электронный ресурс]. – https://man.openbsd.org/sshd_config",
            "Ховард, М. Защищённый код / М. Ховард, Д. Лебланк. – М. : Русская редакция, 2004. – 704 с.",
        ],
        1,
    ):
        pdf.body(14)
        pdf.multi_cell(0, 7.5, f"{i}. {s}", align="J", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

    pdf.output(str(OUT))
    (ROOT.parent / OUT.name).write_bytes(OUT.read_bytes())
    return OUT


if __name__ == "__main__":
    print(build())
