#!/usr/bin/env python3
"""Отчёт lab 1.2 — БГУИР, Струнец Д.П. 321701."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
OUT = ROOT / "Отчет_ЛР1.2_Струнец_ДП_321701.pdf"
LAB = ROOT.parent

FONT = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
COURIER = "/System/Library/Fonts/Supplemental/Courier New.ttf"


class Report(FPDF):
    def __init__(self) -> None:
        super().__init__(format="A4", unit="mm")
        self.set_auto_page_break(auto=True, margin=20)
        self.add_font("TimesNR", "", FONT)
        self.add_font("TimesNR", "B", FONT_B)
        self.add_font("CourierNR", "", COURIER)
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
        self.multi_cell(self.epw, 7.5, " " * 8 + text, align="J", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
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
        self.multi_cell(self.epw - 8, 7.5, "– " + text, align="J", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def caption(self, title: str) -> None:
        self.fig += 1
        self.body(12)
        self.multi_cell(0, 6, f"Рисунок {self.fig} – {title}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def shot(self, name: str, title: str, max_h: float = 90) -> None:
        path = SHOTS / name
        if not path.exists():
            self.para(f"[нет файла {name}]")
            return
        if self.get_y() + max_h + 18 > self.h - self.b_margin:
            self.add_page()
        self.image(str(path), x=self.l_margin, w=self.epw, h=max_h, keep_aspect_ratio=True)
        self.ln(2)
        self.caption(title)

    def code_block(self, lines: list[str], size: float = 9) -> None:
        self.set_font("CourierNR", "", size)
        for line in lines:
            if self.get_y() > self.h - self.b_margin - 12:
                self.add_page()
                self.set_font("CourierNR", "", size)
            self.multi_cell(0, 4.2, line[:110], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)


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
    pdf.ln(26)
    for line in (
        "ОТЧЁТ",
        "по лабораторной работе № 1 (часть 2)",
        "по дисциплине",
        "«Проектирование защищенных интеллектуальных",
        "информационных систем»",
    ):
        pdf.multi_cell(0, 7.5, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.body(14)
    pdf.multi_cell(
        0,
        7.5,
        "Тема: Управление доступом к СУБД PostgreSQL",
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln(35)
    pdf.set_xy(105, pdf.get_y())
    pdf.multi_cell(
        80,
        7.5,
        "Выполнил:\nстудент группы 321701\nСтрунец Д. П.\n\nПроверил:\nСальников Д. А.",
        align="L",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
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
        "Целью работы является настройка и проверка политики контроля доступа "
        "выбранной СУБД. Согласно заданию необходимо создать программы для: "
        "установки СУБД; настройки ролей доступа; проверки политики; удаления "
        "созданных объектов."
    )
    pdf.para("Требуемая политика безопасности:")
    for t in (
        "администратор — полный доступ ко всем подсистемам;",
        "пользователь — полные либо частичные права в предоставленной подсистеме;",
        "гость — только чтение отдельных фрагментов, разрешённых администратором.",
    ):
        pdf.bullet(t)
    pdf.ln(1)
    pdf.para(
        "В качестве варианта выбрана реляционная СУБД PostgreSQL, разворачиваемая "
        "в контейнере Docker. Автоматизация выполнена на языке Python."
    )

    pdf.h1("2 Краткое описание выбранной СУБД")
    pdf.para(
        "PostgreSQL — объектно-реляционная СУБД с развитой моделью ролей и прав "
        "(GRANT/REVOKE) на уровне баз, схем, таблиц и последовательностей. "
        "Разграничение доступа реализуется внутри СУБД независимо от прав ОС: "
        "субъект (роль) получает ровно те операции, которые явно выданы. В работе "
        "использован образ postgres:16-alpine, порт 5432, суперпользователь "
        "контейнера — postgres."
    )

    pdf.h1("3 Описание созданных программ")
    pdf.h2("3.1 Состав программ")
    for t in (
        "docker-compose.yml — установка/запуск PostgreSQL (контейнер psiiz-postgres);",
        "configure.py — создание ролей lab_admin / lab_user / lab_guest, БД psiiz_demo, таблиц и GRANT;",
        "test.py — проверка разрешённых и запрещённых операций для каждой роли;",
        "cleanup.py — удаление БД, ролей и служебного состояния lab_state.json;",
        "db.py — общие параметры подключения.",
    ):
        pdf.bullet(t)

    pdf.h2("3.2 Настроенная политика")
    pdf.para(
        "lab_admin создаётся с атрибутами SUPERUSER/CREATEDB/CREATEROLE и является "
        "владельцем базы — полный доступ. lab_user получает SELECT/INSERT/UPDATE/DELETE "
        "на public_data и только SELECT на confidential_data. lab_guest получает "
        "только SELECT на public_data; доступ к confidential_data запрещён."
    )
    pdf.para("Фрагмент назначения прав в configure.py:")
    cfg = (LAB / "configure.py").read_text(encoding="utf-8").splitlines()
    pdf.code_block(cfg[78:90], size=9)

    pdf.h2("3.3 Результаты проверки")
    pdf.para(
        "Программа test.py подключается от имени каждой роли и фиксирует успех "
        "или отказ (permission denied). Все ожидаемые разрешения и запреты "
        "подтверждены (см. журнал lab_1_2_results.log)."
    )
    pdf.shot("01_install.png", "Запуск PostgreSQL в Docker", 70)
    pdf.shot("02_configure.png", "Создание ролей, базы и GRANT", 85)
    pdf.shot("03_test.png", "Результаты проверки политики доступа", 110)
    pdf.shot("04_cleanup.png", "Удаление базы, ролей и контейнера", 80)

    pdf.para("Фрагмент проверок для роли user (запись в confidential запрещена):")
    tst = (LAB / "test.py").read_text(encoding="utf-8").splitlines()
    pdf.code_block(tst[84:92], size=9)

    pdf.h1("4 Вывод")
    pdf.para(
        "Семантическая составляющая. На примере PostgreSQL показано, как "
        "принцип наименьших привилегий реализуется ролями СУБД: администратор "
        "управляет всеми объектами, пользователь работает в рамках выданных "
        "прав, гость ограничен чтением публичных данных."
    )
    pdf.para(
        "Прагматическая составляющая. Подготовлен набор скриптов install → "
        "configure → test → cleanup, позволяющий воспроизводимо демонстрировать "
        "политику доступа и сравнивать её с разграничением прав на уровне ОС "
        "(лабораторная работа № 1, часть 1)."
    )

    pdf.h1("Список использованных источников")
    for i, s in enumerate(
        [
            "Ховард, М. Защищённый код / М. Ховард, Д. Лебланк. – М. : Русская редакция, 2004. – 704 с.",
            "PostgreSQL Documentation. Privileges [Электронный ресурс]. – Режим доступа: https://www.postgresql.org/docs/current/ddl-privs.html.",
            "CWE – Common Weakness Enumeration [Электронный ресурс]. – Режим доступа: https://cwe.mitre.org/.",
        ],
        1,
    ):
        pdf.body(14)
        pdf.multi_cell(0, 7.5, f"{i}. {s}", align="J", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

    pdf.output(str(OUT))
    copy = LAB / OUT.name
    copy.write_bytes(OUT.read_bytes())
    return OUT


if __name__ == "__main__":
    print(build())
