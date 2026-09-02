#!/usr/bin/env python3
"""Генерация отчёта lab 2.1 в формате, близком к требованиям БГУИР / СТП."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
OUT = ROOT / "Отчет_ЛР2.1_Струнец_ДП_321701.pdf"

FONT = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
FONT_I = "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"


class Report(FPDF):
    def __init__(self) -> None:
        super().__init__(format="A4", unit="mm")
        self.set_auto_page_break(auto=True, margin=20)
        # имя семейства не должно совпадать с core-font Times
        self.add_font("TimesNR", "", FONT)
        self.add_font("TimesNR", "B", FONT_B)
        self.add_font("TimesNR", "I", FONT_I)
        self.fig = 0

    def header(self) -> None:
        return

    def footer(self) -> None:
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("TimesNR", "", 12)
        self.cell(0, 8, str(self.page_no()), align="R")

    def set_body_font(self, size: float = 14) -> None:
        self.set_font("TimesNR", "", size)

    def set_bold(self, size: float = 14) -> None:
        self.set_font("TimesNR", "B", size)

    def p(self, text: str, *, first_indent: float = 12.5, align: str = "J") -> None:
        self.set_body_font(14)
        self.set_x(self.l_margin)
        self.multi_cell(
            0,
            7,
            text,
            align=align,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            markdown=False,
        )
        # emulate first-line indent via leading spaces is unreliable;
        # write with indent using explicit left margin shift for first line
        # FPDF multi_cell doesn't support first-line indent natively well —
        # we prepend thin spaces approx 1.25cm for paragraphs.
        _ = first_indent

    def para(self, text: str) -> None:
        """Абзац с красной строкой ~1,25 см, интервал ~одинарный/чуть больше."""
        self.set_body_font(14)
        usable = self.epw
        # first line with indent
        indent = " " * 8  # визуальный отступ ≈ 1,25 см для Times 14
        self.multi_cell(
            usable,
            7.5,
            indent + text,
            align="J",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(1)

    def h1(self, text: str) -> None:
        self.ln(4)
        self.set_bold(14)
        self.multi_cell(0, 8, text.upper(), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def h2(self, text: str) -> None:
        self.ln(3)
        self.set_bold(14)
        self.multi_cell(0, 7.5, text, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def bullet(self, text: str) -> None:
        self.set_body_font(14)
        self.set_x(self.l_margin + 8)
        self.multi_cell(
            self.epw - 8,
            7.5,
            "– " + text,
            align="J",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    def caption(self, title: str) -> None:
        self.fig += 1
        self.set_body_font(12)
        self.multi_cell(
            0,
            6,
            f"Рисунок {self.fig} – {title}",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(3)

    def add_shot(self, name: str, title: str, max_h: float = 110) -> None:
        path = SHOTS / name
        if not path.exists():
            self.para(f"[нет файла {name}]")
            return
        # leave space for image + caption
        if self.get_y() + max_h + 20 > self.h - self.b_margin:
            self.add_page()
        x = self.l_margin
        w = self.epw
        self.image(str(path), x=x, w=w, h=max_h, keep_aspect_ratio=True)
        self.ln(2)
        self.caption(title)


def title_page(pdf: Report) -> None:
    pdf.add_page()
    pdf.set_margins(left=30, top=20, right=15)
    pdf.set_bold(14)
    lines = [
        "Министерство образования Республики Беларусь",
        "Учреждение образования",
        "«Белорусский государственный университет",
        "информатики и радиоэлектроники»",
        "",
        "Факультет информационных технологий и управления",
        "Кафедра интеллектуальных информационных технологий",
    ]
    for line in lines:
        pdf.multi_cell(0, 7, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(28)
    pdf.set_bold(14)
    for line in (
        "ОТЧЁТ",
        "по лабораторной работе № 2 (часть 1)",
        "по дисциплине",
        "«Проектирование защищенных интеллектуальных",
        "информационных систем»",
    ):
        pdf.multi_cell(0, 7.5, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(10)
    pdf.set_body_font(14)
    pdf.multi_cell(
        0,
        7.5,
        "Тема: Оценка защищённости разработанного приложения VulnNotes",
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    pdf.ln(35)
    pdf.set_body_font(14)
    # right block
    x0 = 105
    pdf.set_xy(x0, pdf.get_y())
    block = (
        "Выполнил:\n"
        "студент группы 321701\n"
        "Струнец Д. П.\n\n"
        "Проверил:\n"
        "Сальников Д. А."
    )
    pdf.multi_cell(80, 7.5, block, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(-35)
    pdf.set_body_font(14)
    pdf.multi_cell(0, 7.5, "Минск 2026", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def build() -> Path:
    pdf = Report()
    pdf.set_margins(left=30, top=20, right=15)
    title_page(pdf)

    # ---- 1 ----
    pdf.add_page()
    pdf.h1("1 Постановка задачи")
    pdf.para(
        "Целью лабораторной работы является разработка учебно-демонстрационного "
        "веб-приложения с функциями управления пользователями и данными, а также "
        "выполнение анализа его защищённости с точки зрения политики безопасности "
        "операционной системы, компонентов приложения и их взаимодействия, сетевой "
        "политики и конфиденциальности данных."
    )
    pdf.para("В соответствии с заданием приложение должно обеспечивать:")
    for t in (
        "добавление пользователя в систему (регистрация);",
        "авторизацию пользователя по идентификационным данным;",
        "создание, редактирование, удаление и поиск конфиденциальных данных;",
        "создание, редактирование, удаление и поиск неконфиденциальных данных;",
        "деавторизацию авторизованного пользователя (logout).",
    ):
        pdf.bullet(t)
    pdf.ln(2)
    pdf.para(
        "Дополнительно приложение подготовлено как стенд для последующей части "
        "работы (лабораторная работа № 2, часть 2) и намеренно содержит типовые "
        "уязвимости по классификации OWASP Top 10:2025, что позволяет наглядно "
        "продемонстрировать последствия ошибок проектирования и реализации."
    )

    # ---- 2 ----
    pdf.h1("2 Краткое описание разработанного приложения")
    pdf.para(
        "Разработано веб-приложение VulnNotes на языке Python (фреймворк Flask) "
        "с хранением данных в SQLite. Приложение упаковано в контейнер Docker на "
        "базе Ubuntu 22.04 и доступно по адресу http://localhost:5050. Процесс "
        "приложения выполняется от непривилегированного пользователя appuser."
    )
    pdf.para("Основные функции и маршруты:")
    for t in (
        "регистрация – /register; вход – /login; выход – /logout;",
        "публичные заметки (CRUD) – /public;",
        "конфиденциальные заметки (CRUD) – /confidential;",
        "поиск по заметкам – /search;",
        "карта уязвимостей – /vulns.",
    ):
        pdf.bullet(t)
    pdf.ln(2)
    pdf.para(
        "Для демонстрации предусмотрены учётные записи: admin/admin, alice/alice, "
        "bob/bob123, guest/guest. Ниже приведены снимки экрана основных сценариев."
    )

    pdf.add_shot("13_register.png", "Страница регистрации пользователя", max_h=85)
    pdf.add_shot("01_login.png", "Страница авторизации", max_h=85)
    pdf.add_shot("02_home.png", "Главная страница после входа (пользователь alice)", max_h=95)
    pdf.add_shot("03_public.png", "Список публичных (неконфиденциальных) заметок", max_h=95)
    pdf.add_shot("04_confidential.png", "Список конфиденциальных заметок пользователя", max_h=95)
    pdf.add_shot("06_search_cookies.png", "Страница поиска; демонстрация чтения cookie сессии", max_h=100)

    # ---- 3 ----
    pdf.h1("3 Анализ защищённости приложения")
    pdf.h2("3.1 Политика безопасности операционной системы")
    pdf.para(
        "Приложение развёрнуто в контейнере Ubuntu 22.04. Положительные стороны: "
        "процесс Flask не запускается от root, а от пользователя appuser; "
        "изолирована файловая система контейнера. Вместе с тем в образе намеренно "
        "оставлены учебные векторы повышения привилегий (SUID-утилита backup-tool, "
        "sudo NOPASSWD для find), что снижает защищённость ОС-контура и "
        "моделирует типичные ошибки администрирования."
    )
    pdf.h2("3.2 Политика безопасности компонентов и их взаимодействия")
    pdf.para(
        "Компоненты: веб-сервер Flask, СУБД SQLite (файл /app/data/app.db), "
        "сессионные cookie браузера. Взаимодействие реализовано через HTTP без TLS. "
        "Выявлены нарушения: SQL-инъекции в /login и /search; отражённый XSS на "
        "/search; IDOR при доступе к /confidential/<id>; открытый API "
        "/api/notes/<id> без авторизации; небезопасная десериализация pickle на "
        "/import; SSRF на /fetch; DEBUG=True и эндпоинт /debug/config с утечкой "
        "secret_key; пароли в БД в открытом виде; SESSION_COOKIE_HTTPONLY=False."
    )
    pdf.add_shot("09_vulns.png", "Карта уязвимостей OWASP Top 10:2025 в приложении", max_h=120)
    pdf.add_shot("12_sqli_login.png", "Обход авторизации SQL-инъекцией в поле username", max_h=90)
    pdf.add_shot("05_idor.png", "IDOR: alice читает чужую конфиденциальную заметку /confidential/1", max_h=80)
    pdf.add_shot("11_xss_cookies.png", "XSS: вывод document.cookie (кража сессии)", max_h=110)
    pdf.add_shot("08_debug.png", "Утечка конфигурации через /debug/config", max_h=70)
    pdf.add_shot("07_sql_error.png", "Утечка текста SQL и исключения при ошибочном запросе", max_h=90)
    pdf.add_shot("10_ssrf.png", "Интерфейс SSRF (/fetch) – сервер выполняет произвольный HTTP-запрос", max_h=75)

    pdf.h2("3.3 Сетевая политика безопасности")
    pdf.para(
        "Сервис слушает 0.0.0.0:5000 внутри контейнера и публикуется на хост "
        "как localhost:5050. Передача идентификационных данных идёт по HTTP "
        "(без шифрования канала), cookie сессии не имеет флага Secure. Отсутствуют "
        "ограничения частоты запросов (rate limit), что облегчает перебор паролей. "
        "SSRF позволяет обращаться к внутренним ресурсам контейнера "
        "(например, http://127.0.0.1:5000/debug/config)."
    )
    pdf.h2("3.4 Сводка по OWASP Top 10:2025")
    pdf.para(
        "В приложении воспроизведены категории A01–A10 (2025): Broken Access Control "
        "(в т.ч. SSRF), Security Misconfiguration, Software Supply Chain Failures, "
        "Cryptographic Failures, Injection, Insecure Design, Authentication Failures, "
        "Software/Data Integrity Failures, Security Logging Failures, Mishandling of "
        "Exceptional Conditions. Подробная карта доступна на странице /vulns и в "
        "сопроводительной документации лабораторной работы."
    )

    # ---- 4 ----
    pdf.h1("4 Анализ защищённости конфиденциальной информации")
    pdf.para(
        "Конфиденциальные заметки хранятся в таблице confidential_notes без "
        "шифрования «на диске». Разграничение доступа на уровне списка "
        "(WHERE owner_id = ?) легко обходится IDOR и неавторизованным API. "
        "Пароли пользователей хранятся в открытом виде, поэтому компрометация "
        "файла БД приводит к полной утрате учётных данных. Cookie сессии доступна "
        "JavaScript (отсутствие HttpOnly), что в сочетании с XSS позволяет "
        "похитить сессию и выдать себя за пользователя."
    )
    pdf.para(
        "Таким образом, конфиденциальность данных в текущей реализации не "
        "обеспечена: нарушены принципы least privilege, secure defaults, "
        "defense in depth и безопасной обработки ошибок."
    )
    pdf.para("Рекомендации по повышению защищённости (для исправленной версии):")
    for t in (
        "параметризованные SQL-запросы и экранирование вывода (защита от SQLi/XSS);",
        "проверка владельца ресурса на каждом CRUD-операции; аутентификация API;",
        "хэширование паролей (bcrypt/argon2), TLS, флаги cookie HttpOnly/Secure/SameSite;",
        "отключение DEBUG, удаление /debug/config, единый обработчик ошибок без утечек;",
        "запрет pickle от пользователя; allowlist для SSRF; rate limit и аудит логов;",
        "шифрование at-rest для confidential_notes и жёсткая политика ОС (без лишнего SUID).",
    ):
        pdf.bullet(t)

    # ---- 5 ----
    pdf.h1("5 Вывод")
    pdf.para(
        "Семантическая составляющая. В ходе работы реализовано веб-приложение "
        "VulnNotes, поддерживающее регистрацию, авторизацию, logout, CRUD и поиск "
        "публичных и конфиденциальных данных. Выполнен анализ защищённости с "
        "точки зрения ОС, компонентов, сети и конфиденциальности; идентифицированы "
        "критические дефекты, соответствующие актуальным категориям OWASP Top 10:2025."
    )
    pdf.para(
        "Прагматическая составляющая. Полученный стенд пригоден для демонстрации "
        "атак и последующей отработки методов эксплуатации и повышения "
        "привилегий (лабораторная работа № 2, часть 2). Результаты анализа "
        "показывают, что без целенаправленных мер защиты даже функционально "
        "полное приложение не обеспечивает сохранность конфиденциальной информации."
    )

    # ---- sources ----
    pdf.h1("Список использованных источников")
    sources = [
        "Ховард, М. Защищённый код / М. Ховард, Д. Лебланк. – М. : Русская редакция, 2004. – 704 с.",
        "Ховард, М. 24 смертных греха компьютерной безопасности / М. Ховард, Д. Лебланк, Дж. Вьега. – СПб. : Питер, 2010. – 400 с.",
        "OWASP Top 10:2025 [Электронный ресурс]. – Режим доступа: https://owasp.org/Top10/2025/.",
        "Flask Documentation [Электронный ресурс]. – Режим доступа: https://flask.palletsprojects.com/.",
    ]
    pdf.set_body_font(14)
    for i, s in enumerate(sources, 1):
        pdf.multi_cell(
            0,
            7.5,
            f"{i}. {s}",
            align="J",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
