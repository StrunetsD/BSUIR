#!/usr/bin/env python3
"""Отчёт lab 2.2 — оценка защищённости VulnNotes (система из 2.1)."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
OUT = ROOT / "Отчет_ЛР2.2_Струнец_ДП_321701.pdf"

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
            self.para(f"[нет файла {name}]")
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
        "по лабораторной работе № 2 (часть 2)",
        "по дисциплине",
        "«Проектирование защищенных интеллектуальных",
        "информационных систем»",
    ):
        pdf.multi_cell(0, 7.5, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.body(14)
    pdf.multi_cell(
        0, 7.5,
        "Тема: Оценка защищённости сторонней системы VulnNotes",
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

    # 1
    pdf.add_page()
    pdf.h1("1 Постановка задачи")
    pdf.para(
        "Целью лабораторной работы является разработка методики оценки "
        "защищённости сторонних программных систем и применение этой методики "
        "к предоставленному приложению (результат лабораторной работы № 2, "
        "часть 1 — веб-приложение VulnNotes). Необходимо выполнить анализ по "
        "политике безопасности ОС, компонентов и их взаимодействия, сетевой "
        "политике и конфиденциальности данных; предложить меры "
        "усовершенствования и рекомендации по безопасному использованию."
    )

    # 2
    pdf.h1("2 Краткое описание предоставленной системы")
    pdf.para(
        "VulnNotes — учебно-демонстрационное веб-приложение на Flask + SQLite, "
        "развёрнутое в контейнере Docker (Ubuntu 22.04), UI: http://localhost:5050. "
        "Функции: регистрация/авторизация/logout, CRUD публичных и "
        "конфиденциальных заметок, поиск. Процесс выполняется от пользователя "
        "appuser. В приложении намеренно присутствуют уязвимости OWASP Top 10:2025 "
        "для целей обучения и анализа."
    )
    pdf.shot("02_home.png", "Главная страница VulnNotes после авторизации", 90)
    pdf.shot("09_vulns.png", "Встроенная карта уязвимостей OWASP Top 10:2025", 115)

    # 3
    pdf.h1("3 Разработанная методика оценки защищённости")
    pdf.para(
        "Методика представляет собой многоуровневый чек-лист с фиксацией "
        "находок, уровня риска (критический / высокий / средний / низкий) и "
        "доказательств (скриншот, HTTP-запрос, лог). Этапы:"
    )
    for t in (
        "Инвентаризация: границы системы, роли, данные (публичные / конфиденциальные), порты, зависимости.",
        "Анализ ОС и окружения: пользователь процесса, SUID/sudo, секреты на диске, изоляция контейнера.",
        "Анализ компонентов: веб-фреймворк, СУБД, библиотеки (версии, известные CVE), сериализация, debug-режимы.",
        "Анализ взаимодействия: аутентификация, авторизация (IDOR), API, SSRF, cookie-флаги, каналы HTTP/TLS.",
        "Анализ конфиденциальности: хранение паролей/PII, шифрование at-rest, утечки в ошибках и логах.",
        "Динамическая проверка (black-box): SQLi, XSS, brute force, доступ к чужим ресурсам, сканеры по необходимости.",
        "Организационный уровень: политики паролей, аудит, реагирование на инциденты.",
        "Документирование: сводная таблица находок → рекомендации по устранению и безопасной эксплуатации.",
    ):
        pdf.bullet(t)
    pdf.ln(2)
    pdf.para(
        "Критерий приемлемости: отсутствие критических и высоких дефектов в "
        "контуре аутентификации, авторизации и хранения секретов; наличие "
        "журналирования security-событий; TLS и безопасные cookie в production."
    )

    # 4
    pdf.h1("4 Анализ защищённости по разработанной методике")
    pdf.h2("4.1 Политика безопасности операционной системы")
    pdf.para(
        "Положительно: процесс Flask не от root (appuser). Отрицательно: в образе "
        "оставлены учебные векторы повышения привилегий (SUID backup-tool, "
        "sudo find NOPASSWD), на диске доступны подсказки пароля "
        "(/opt/backup/.root_hint, ~/.env). Риск: компрометация веб-приложения "
        "легко переходит в root внутри контейнера."
    )
    pdf.h2("4.2 Компоненты и их взаимодействие")
    pdf.para(
        "Выявлены: SQL-инъекция в /login и /search; XSS на /search; IDOR "
        "/confidential/<id>; неавторизованный API /api/notes/<id>; pickle "
        "deserialization на /import; SSRF /fetch; DEBUG=True и /debug/config с "
        "утечкой secret_key; пароли в plaintext; SESSION_COOKIE_HTTPONLY=False; "
        "отсутствие rate limit и security-логов."
    )
    pdf.shot("12_sqli_login.png", "Обход аутентификации SQL-инъекцией", 85)
    pdf.shot("05_idor.png", "IDOR: доступ к чужой конфиденциальной заметке", 75)
    pdf.shot("11_xss_cookies.png", "XSS: кража session cookie через document.cookie", 100)
    pdf.shot("08_debug.png", "Утечка конфигурации через /debug/config", 65)
    pdf.shot("07_sql_error.png", "Утечка SQL и текста исключения клиенту", 85)
    pdf.shot("10_ssrf.png", "SSRF: сервер выполняет произвольный HTTP-запрос", 70)
    pdf.shot("06_search_cookies.png", "Cookie сессии доступна JavaScript (нет HttpOnly)", 90)

    pdf.h2("4.3 Сетевая политика безопасности")
    pdf.para(
        "Сервис слушает 0.0.0.0 внутри контейнера, публикация на хост :5050. "
        "Трафик без TLS; cookie без Secure. SSRF позволяет обращаться к "
        "внутренним адресам (127.0.0.1). Сетевых ACL/WAF нет."
    )
    pdf.h2("4.4 Конфиденциальность данных")
    pdf.para(
        "Конфиденциальные заметки и пароли хранятся открытым текстом в SQLite. "
        "Разграничение на уровне списка обходится IDOR и открытым API. XSS + "
        "отсутствие HttpOnly приводит к угону сессии. Итог: конфиденциальность "
        "не обеспечивается."
    )
    pdf.h2("4.5 Сводная оценка")
    pdf.para(
        "По методике система оценивается как не готовая к эксплуатации: "
        "множество критических дефектов (A01, A04, A05, A07, A08 по OWASP "
        "Top 10:2025). Приложение пригодно только как учебный стенд."
    )

    # 5
    pdf.h1("5 Комплекс мер по усовершенствованию")
    for t in (
        "Параметризованные SQL-запросы; экранирование/шаблоны без |safe для пользовательского ввода.",
        "Проверка владельца на каждой операции с confidential; аутентификация API; запрет IDOR.",
        "Хэширование паролей (argon2/bcrypt); TLS; cookie: HttpOnly, Secure, SameSite=Lax/Strict.",
        "Отключить DEBUG; удалить /debug/config; единый error handler без утечки стека/SQL.",
        "Запретить pickle от клиента (JSON); allowlist URL для исходящих запросов (анти-SSRF).",
        "Rate limit / lockout на /login; MFA для admin; политика сложности паролей.",
        "Журналирование failed login, IDOR, admin-действий; алерты.",
        "Шифрование at-rest для confidential_notes; ротация secret_key.",
        "Убрать учебные SUID/sudo; secrets только через env/secret store; non-root + read-only FS.",
        "Зафиксировать зависимости (lock + hashes), SBOM, регулярный audit/CVE-scan.",
    ):
        pdf.bullet(t)

    # 6
    pdf.h1("6 Рекомендации по безопасному использованию")
    for t in (
        "Не размещать VulnNotes в публичной сети и не использовать реальные персональные данные.",
        "Держать стенд только в изолированной Docker-сети / локальном хосте; ограничить порт firewall.",
        "Учётные записи демо (admin/admin и т.п.) менять при любом внешнем доступе.",
        "После практики выполнять docker compose down -v; не оставлять контейнер с SUID-векторами.",
        "Для «боевой» версии применять меры раздела 5 и проводить повторную оценку по методике раздела 3.",
        "Разделять роли разработчика и администратора стенда; не выполнять приложение от root на хосте.",
    ):
        pdf.bullet(t)

    # 7
    pdf.h1("7 Вывод")
    pdf.para(
        "Семантическая составляющая. Разработана многоуровневая методика оценки "
        "защищённости (ОС, компоненты, сеть, данные, динамика, организация) и "
        "применена к системе VulnNotes. Подтверждены критические нарушения "
        "аутентификации, авторизации, криптографии и целостности обработки данных."
    )
    pdf.para(
        "Прагматическая составляющая. Сформированы конкретные меры устранения "
        "дефектов и правила безопасной эксплуатации учебного стенда. Методика "
        "может повторно применяться к другим сторонним системам (сканеры + "
        "ручной анализ по чек-листу)."
    )

    pdf.h1("Список использованных источников")
    for i, s in enumerate(
        [
            "Ховард, М. Защищённый код / М. Ховард, Д. Лебланк. – М. : Русская редакция, 2004. – 704 с.",
            "Ховард, М. 24 смертных греха компьютерной безопасности / М. Ховард, Д. Лебланк, Дж. Вьега. – СПб. : Питер, 2010. – 400 с.",
            "OWASP Top 10:2025 [Электронный ресурс]. – Режим доступа: https://owasp.org/Top10/2025/.",
            "CWE – Common Weakness Enumeration [Электронный ресурс]. – Режим доступа: https://cwe.mitre.org/.",
            "OWASP Vulnerability Scanning Tools [Электронный ресурс]. – Режим доступа: https://owasp.org/www-community/Vulnerability_Scanning_Tools.",
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
