#!/usr/bin/env python3
"""Отчёт lab 1.1 — БГУИР, Струнец Д.П. 321701."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
OUT = ROOT / "Отчет_ЛР1.1_Струнец_ДП_321701.pdf"
CODE = ROOT.parent / "lab_1_1.sh"

FONT = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
FONT_I = "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"
COURIER = "/System/Library/Fonts/Supplemental/Courier New.ttf"


class Report(FPDF):
    def __init__(self) -> None:
        super().__init__(format="A4", unit="mm")
        self.set_auto_page_break(auto=True, margin=20)
        self.add_font("TimesNR", "", FONT)
        self.add_font("TimesNR", "B", FONT_B)
        self.add_font("TimesNR", "I", FONT_I)
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
        "по лабораторной работе № 1 (часть 1)",
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
        "Тема: Управление доступом к объектам операционных систем",
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
        "Целью работы является изучение модели избирательного управления доступом "
        "в UNIX-подобных ОС и практическая настройка прав на объекты файловой "
        "системы (пользователь / группа / остальные), а также проверка корректности "
        "этих прав для набора субъектов доступа."
    )
    pdf.para("Требуется создать программу (скрипт), которая:")
    for t in (
        "создаёт группы group_iit1, group_iit2 и пользователей iit11, iit12, iit21, iit22, iit3;",
        "назначает iit21 административные привилегии;",
        "создаёт каталоги pzs, pzs11–pzs15 с заданными режимами доступа;",
        "от имени iit11 создаёт набор файлов file11–file55 с требуемыми правами;",
        "проверяет чтение, запись, исполнение файлов и операции над каталогами;",
        "проверяет возможность остановки процессов file*5;",
        "удаляет созданные объекты, пользователей и группы.",
    ):
        pdf.bullet(t)

    pdf.h1("2 Описание созданной программы")
    pdf.h2("2.1 Назначение и решаемые задачи")
    pdf.para(
        "Программа реализована в виде bash-скрипта lab_1_1.sh. Скрипт предназначен "
        "для автоматизации пунктов задания 1–17 на Linux (запуск от root / через sudo). "
        "Результаты проверок записываются в lab_1_1_results.log. Для демонстрации "
        "скрипт выполнялся в контейнере Ubuntu 22.04."
    )
    pdf.para("Основные функции скрипта:")
    for t in (
        "create_groups_and_users — группы, пользователи, sudo для iit21;",
        "create_directories / create_files_in_dir — каталоги и файлы с chmod/chown;",
        "check_file_access — матрица read/write/exec для iit11, iit12, iit21, iit22, iit3, root;",
        "check_process_kill — запуск file*5 и попытки kill от разных пользователей;",
        "check_dir_ops — list/create/delete для pzs11–pzs15;",
        "final_cleanup — удаление каталога pzs, пользователей и групп.",
    ):
        pdf.bullet(t)

    pdf.h2("2.2 Фрагмент кода программы")
    pdf.para("Ниже приведён ключевой фрагмент функции создания каталогов и назначения режимов:")
    code = CODE.read_text(encoding="utf-8").splitlines()
    # строки create_directories
    snippet = code[85:122] if len(code) > 122 else code[:40]
    pdf.code_block(snippet, size=8.5)
    pdf.para("Фрагмент проверки доступа к файлам:")
    pdf.code_block(code[253:268], size=8.5)

    pdf.h2("2.3 Результаты работы")
    pdf.para(
        "Скрипт последовательно создал субъекты и объекты доступа, сформировал дерево "
        "каталогов pzs*, выполнил проверки и завершил очистку. Ниже приведены "
        "снимки фрагментов журнала выполнения."
    )
    pdf.shot("01_setup.png", "Создание групп, пользователей и каталогов pzs11–pzs15", 88)
    pdf.shot("02_tree.png", "Фрагмент дерева каталогов и прав доступа", 100)
    pdf.shot("03_file_access.png", "Проверка прав чтения/записи/исполнения файлов", 90)
    pdf.shot("04_proc_kill.png", "Проверка возможности остановить процессы file*5", 85)
    pdf.shot("05_dir_ops.png", "Проверка операций list/create/delete для каталогов", 100)
    pdf.shot("06_cleanup.png", "Удаление файлов, каталогов, пользователей и групп", 80)

    pdf.para(
        "По результатам видно, что доступ определяется классом субъекта (владелец, "
        "группа, остальные, root) и битовой маской режима. Пользователи одной группы "
        "group_iit1 (iit11, iit12) получают групповые права; iit3 действует как "
        "«остальные»; root обходит обычные ограничения UNIX DAC. Каталоги с режимом "
        "070/007 ограничивают операции list/create для субъектов вне целевого класса."
    )

    pdf.h1("3 Вывод")
    pdf.para(
        "Семантическая составляющая. Изучена модель разграничения доступа UNIX "
        "(u/g/o), реализована автоматизация настройки ACL-эквивалентных прав через "
        "chmod/chown и выполнена экспериментальная проверка доступа субъектов к "
        "файлам, каталогам и процессам."
    )
    pdf.para(
        "Прагматическая составляющая. Получен воспроизводимый стенд (lab_1_1.sh + "
        "лог), пригодный для демонстрации политики доступа ОС и для сравнения с "
        "контролем доступа на уровне приложений/СУБД (часть 2 лабораторной работы № 1)."
    )

    pdf.h1("Список использованных источников")
    for i, s in enumerate(
        [
            "Олифер, В. Г. Сетевые операционные системы / В. Г. Олифер, Н. А. Олифер. – 2-е изд. – СПб. : Питер, 2009. – 669 с.",
            "Таненбаум, Э. С. Современные операционные системы / Э. С. Таненбаум. – 3-е изд. – СПб. : Питер, 2011. – 1120 с.",
            "Manual page chmod(1), chown(1), useradd(8) [Электронный ресурс]. – Режим доступа: https://man7.org/linux/man-pages/.",
        ],
        1,
    ):
        pdf.body(14)
        pdf.multi_cell(0, 7.5, f"{i}. {s}", align="J", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

    pdf.output(str(OUT))
    # копия в корень лабы
    copy = ROOT.parent / OUT.name
    copy.write_bytes(OUT.read_bytes())
    return OUT


if __name__ == "__main__":
    print(build())
