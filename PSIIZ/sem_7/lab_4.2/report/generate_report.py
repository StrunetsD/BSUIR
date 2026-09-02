#!/usr/bin/env python3
"""Отчёт lab 4.2 — Suricata IDS/IPS на стенде nginx+SSH."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
OUT = ROOT / "Отчет_ЛР4.2_Струнец_ДП_321701.pdf"

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
        "по лабораторной работе № 4 (часть 2)",
        "по дисциплине",
        "«Проектирование защищенных интеллектуальных",
        "информационных систем»",
    ):
        pdf.multi_cell(0, 7.5, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.body(14)
    pdf.multi_cell(
        0, 7.5,
        "Тема: IDS/IPS Suricata на удалённом сервере",
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
        "Целью работы является установка и настройка системы обнаружения "
        "(и демонстрация реакции предотвращения) вторжений на удалённом "
        "сервере, анализ журналов подсистем до и после включения средств "
        "IDS/IPS, оформление отчёта."
    )
    pdf.para(
        "Вариант: Suricata. Стенд продолжает лабораторную работу № 4.1 "
        "(nginx + OpenSSH в Docker). Порты хоста: HTTP — 8081, SSH — 2223. "
        "Suricata разделяет network namespace с сервером (network_mode: "
        "service:server) и анализирует трафик на интерфейсе eth0."
    )

    pdf.h1("2 Описание установленного ПО (Suricata)")
    pdf.para(
        "Suricata — открытая IDS/IPS/NSM-система (OISF). Назначение: "
        "сигнатурный и протокольный анализ сетевого трафика в реальном "
        "времени, запись событий (eve.json, fast.log), опционально "
        "блокировка (IPS через NFQUEUE/AF_PACKET IPS)."
    )
    pdf.para("Режимы работы:")
    for t in (
        "IDS (detection): пассивный просмотр (AF_PACKET / SPAN), алерты без изменения трафика;",
        "IPS (prevention): inline — drop/reject по правилам;",
        "NSM: журналирование HTTP/DNS/TLS и др. для расследования.",
    ):
        pdf.bullet(t)
    pdf.para(
        "В работе использован образ jasonish/suricata:7.0.3 в режиме IDS "
        "(AF_PACKET на eth0). Учебные правила lab42.rules детектируют "
        "HTTP-пробы (/admin, wp-login, .env, phpmyadmin, .git), "
        "User-Agent sqlmap/zgrab/masscan и SSH к порту 22. Принцип: "
        "захват пакетов → разбор протоколов → сопоставление сигнатур → "
        "запись alert в eve.json/fast.log. Реакция IPS смоделирована "
        "скриптом ips_response_demo.sh (список IP для iptables/fail2ban)."
    )
    pdf.shot("01_compose.png", "Схема docker-compose (server + Suricata)", 85)
    pdf.shot("07_running.png", "Работа контейнеров и HTTP 200", 70)
    pdf.shot("02_rules.png", "Фрагмент учебных правил Suricata", 95)

    pdf.h1("3 Краткое описание анализируемых подсистем")
    for t in (
        "Веб-сервер nginx — HTTP-запросы к тестовой странице и чувствительным URI;",
        "OpenSSH (sshd) — попытки аутентификации (успешные и Failed password);",
        "Suricata — сетевые события и алерты по правилам lab42.rules.",
    ):
        pdf.bullet(t)

    pdf.h1("4 Описание анализируемых файлов")
    pdf.h2("4.1 Журналы сервера (как в 4.1)")
    pdf.para(
        "access.log (nginx combined) — URI, коды ответа, User-Agent, IP. "
        "auth.log — Failed/Accepted password sshd. На хосте: "
        "lab_4.2/logs/nginx/, lab_4.2/logs/auth.log."
    )
    pdf.h2("4.2 Журналы Suricata")
    for t in (
        "fast.log — краткие строки алертов (классический формат Snort-like);",
        "eve.json — структурированные события (alert, http, ssh, stats);",
        "suricata.log — служебный журнал движка;",
        "logs/before|after/summary.txt — снимки «до/после» для сравнения;",
        "logs/after/deny_ips.txt — IP-кандидаты на блокировку (IPS-демо).",
    ):
        pdf.bullet(t)

    pdf.h1("5 Анализ до и после настройки IDS/IPS")
    pdf.h2("5.1 До включения Suricata (только nginx/SSH)")
    pdf.para(
        "Без IDS администратор видит лишь прикладные журналы: рост 404 "
        "на /admin, /wp-login.php, /.env, User-Agent sqlmap/zgrab, "
        "Failed password в auth.log. Автоматической классификации "
        "атаки и единого потока алертов нет — разбор ручной "
        "(как в лабораторной работе № 4.1)."
    )
    pdf.shot("03_before.png", "Снимок «до»: сводка access/auth", 90)

    pdf.h2("5.2 После включения Suricata")
    pdf.para(
        "После запуска Suricata и генерации учебного трафика "
        "(scripts/gen_attacks.sh) зафиксировано 92 события alert. "
        "Распределение по сигнатурам: User-Agent sqlmap — 41; "
        "zgrab — 20; HTTP probe admin/wp-login/.env — по 6; "
        "phpmyadmin/.git — по 5; SSH to server — 2; masscan — 1. "
        "Основные источники: контейнер-атакующий в Docker-сети "
        "(172.26.0.3) и адрес хоста через published ports."
    )
    pdf.para(
        "Сравнение: те же аномалии, что в access.log/auth.log, "
        "получают явные сигнатуры и приоритеты в fast.log/eve.json; "
        "скрипт IPS формирует deny-list для блокировки на firewall. "
        "Таким образом политика безопасности дополняется "
        "автоматизированным обнаружением и подготовкой ответа."
    )
    pdf.shot("04_after_alerts.png", "Сводка алертов после атак", 100)
    pdf.shot("05_fast_log.png", "Фрагмент fast.log", 95)
    pdf.shot("06_ips_demo.png", "Демонстрация IPS-ответа (deny IP)", 70)

    pdf.h1("6 Сравнение с аналогами")
    pdf.para(
        "Snort — классическая сигнатурная IDS/IPS; экосистема правил "
        "пересекается с Suricata, но Suricata изначально многопоточна "
        "и сильнее в разборе протоколов/NSM. Bro/Zeek — акцент на "
        "скриптуемом анализе сессий, не на drop-IPS. OSSEC/Wazuh — "
        "host-based IDS (файлы, логи, rootkit), дополняет сетевую "
        "Suricata. Tripwire — контроль целостности ФС. Для сетевого "
        "стенда nginx+SSH выбран Suricata как IDS с возможностью "
        "развития до IPS."
    )

    pdf.h1("7 Вывод")
    pdf.para(
        "Семантическая составляющая. Установлена и настроена Suricata "
        "в режиме IDS на учебном удалённом сервере; показаны назначение, "
        "режимы и принцип работы; проанализированы журналы nginx, SSH "
        "и Suricata до и после включения политики обнаружения."
    )
    pdf.para(
        "Прагматическая составляющая. Получен воспроизводимый "
        "Docker-стенд с правилами, скриптами атак/снимков и демо "
        "IPS-реакции; подтверждено, что сигнатурный анализ повышает "
        "наблюдаемость атак относительно ручного разбора access.log "
        "и auth.log."
    )

    pdf.h1("Список использованных источников")
    for i, s in enumerate(
        [
            "Suricata — Open Source IDS / IPS / NSM engine [Электронный ресурс]. – https://suricata.io/",
            "Suricata User Guide [Электронный ресурс]. – https://docs.suricata.io/",
            "Документация nginx: ngx_http_log_module [Электронный ресурс]. – https://nginx.org/en/docs/http/ngx_http_log_module.html",
            "Официальный сайт Snort [Электронный ресурс]. – https://www.snort.org/",
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
