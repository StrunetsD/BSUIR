#!/usr/bin/env python3
"""Отчёт lab 3.1 — анализ безопасности кода и дампов памяти."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
OUT = ROOT / "Отчет_ЛР3.1_Струнец_ДП_321701.pdf"

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

    def code_block(self, lines: list[str], size: float = 8.5) -> None:
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
    pdf.ln(24)
    for line in (
        "ОТЧЁТ",
        "по лабораторной работе № 3 (часть 1)",
        "по дисциплине",
        "«Проектирование защищенных интеллектуальных",
        "информационных систем»",
    ):
        pdf.multi_cell(0, 7.5, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.body(14)
    pdf.multi_cell(
        0, 7.5,
        "Тема: Анализ безопасности кода и дампов оперативной памяти",
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
        "Целью работы является разработка приложения с интерактивным интерфейсом "
        "для создания, обновления и удаления данных в оперативной памяти "
        "(публичных и конфиденциальных), защита конфиденциальных данных "
        "хешированием или шифрованием, а также анализ безопасности кода, "
        "потребления ресурсов и дампов памяти после create / update / delete."
    )

    pdf.h1("2 Краткое описание разработанного приложения")
    pdf.para(
        "Приложение In-Memory Secure Store реализовано на Python 3 (Tkinter + "
        "библиотека cryptography). Все записи хранятся в словаре MemoryStore "
        "только в RAM процесса. Типы записей: public (открытый текст); "
        "confidential_hash (PBKDF2-HMAC-SHA256, необратимо); confidential_enc "
        "(Fernet/AES, обратимо ключом приложения). Предусмотрены валидация "
        "ввода, просмотр/расшифровка, вызов make_dump.sh и окно просмотра "
        "снимков из каталога dumps/."
    )
    pdf.shot("06_ui_main.png", "Главное окно приложения (CRUD и типы защиты)", 100)
    pdf.shot("05_protect_code.png", "Фрагмент кода защиты конфиденциальных данных", 90)

    pdf.h1("3 Анализ защищённости приложения")
    pdf.para(
        "С точки зрения кода приняты меры: разделение публичных и "
        "конфиденциальных данных; немедленное преобразование секрета в хеш "
        "или шифротекст при create/update; валидация пустых и чрезмерно "
        "длинных значений; сообщение об ошибке вместо падения; удаление "
        "записи из словаря с затиранием полей объекта."
    )
    pdf.para("Ограничения (важно для отчёта по безопасности):")
    for t in (
        "plaintext на короткое время существует в виджете Text и локальных str Python;",
        "ключ Fernet хранится в RAM процесса — дамп процесса theoretically компрометирует ciphertext;",
        "затирание строк в Python не гарантирует очистку всех копий в куче (GC/interning);",
        "полный core-дамп на macOS часто требует прав отладчика (SIP).",
    ):
        pdf.bullet(t)

    pdf.h1("4 Анализ оперативной памяти и процессорного времени")
    pdf.para(
        "Автотест выполнил create → dump → update → dump → delete → dump в одном "
        "процессе. По getrusage: CPU user ≈ 0,064 с, sys ≈ 0,065 с; max RSS ≈ 40 МБ "
        "(типично для интерпретатора Python + cryptography). Утилита make_dump.sh "
        "дополнительно сохраняет ps/resources.txt и vmmap (карта регионов памяти). "
        "Полный файл core в тестовых прогонах на macOS не сформирован без elevated "
        "прав — для анализа использовались store_snapshot, RESULT и vmmap."
    )
    pdf.shot("04_test_log.png", "Протокол автотеста и поиск маркеров в снимках", 100)

    pdf.h1("5 Анализ дампов оперативной памяти")
    pdf.para(
        "Для трассировки вводились маркеры: PUBLIC_MARK_*, SECRET_PLAIN_*, "
        "CARD_PLAIN_*. Поиск выполнялся по текстовым артефактам снимка "
        "(в первую очередь store_snapshot.txt)."
    )
    pdf.h2("5.1 После создания данных")
    pdf.para(
        "В снимке after_create: публичное значение PUBLIC_MARK_qwer присутствует "
        "открытым текстом; для пароля в store лежит 64 hex-символа PBKDF2, "
        "SECRET_PLAIN_hunter2 в snapshot не найден; для карты — ciphertext Fernet "
        "(префикс gAAAAA), CARD_PLAIN в snapshot не найден. Это соответствует "
        "ожидаемой модели хранения после _protect()."
    )
    pdf.shot("01_after_create.png", "Снимок after_create (RESULT + store_snapshot)", 105)

    pdf.h2("5.2 После обновления данных")
    pdf.para(
        "В after_update публичный маркер сменился на PUBLIC_MARK_updated; старый "
        "PUBLIC_MARK_qwer в snapshot отсутствует. Хеш и ciphertext пересчитаны "
        "заново; plaintext SECRET_PLAIN_updated99 / CARD_PLAIN в текстовых "
        "артефактах снимка не обнаружены. Вывод: store отражает актуальное "
        "защищённое представление, однако полный core мог бы сохранить «хвосты» "
        "старых строк в куче."
    )
    pdf.shot("02_after_update.png", "Снимок after_update", 100)

    pdf.h2("5.3 После удаления данных")
    pdf.para(
        "После delete конфиденциальных записей в after_delete осталась одна "
        "публичная запись PUBLIC_MARK_updated; префикс gAAAAA и хеши секретов "
        "из snapshot исчезли. Это показывает корректное удаление из структуры "
        "приложения. Отдельно отмечено: отсутствие строк в snapshot ≠ "
        "гарантированное отсутствие остатков в физической RAM без полного core "
        "и анализа heap."
    )
    pdf.shot("03_after_delete.png", "Снимок after_delete", 90)

    pdf.h2("5.4 Хранение конфиденциальных и неконфиденциальных данных")
    for t in (
        "Неконфиденциальные: plaintext в RAM и в snapshot — ожидаемо и подтверждено поиском маркера.",
        "Конфиденциальные (хеш): в store только PBKDF2; исходник в snapshot после create не найден.",
        "Конфиденциальные (шифр): в store Fernet; расшифровка возможна только с ключом процесса.",
        "Удаление убирает объекты из словаря; для полной санации RAM нужны secure memory / языки с ручным управлением буферами.",
    ):
        pdf.bullet(t)

    pdf.h1("6 Вывод")
    pdf.para(
        "Семантическая составляющая. Реализовано UI-приложение с CRUD в оперативной "
        "памяти, разделением типов данных и защитой секретов хешированием/шифрованием; "
        "выполнен анализ кода, ресурсов и трёх снимков памяти по сценарию задания."
    )
    pdf.para(
        "Прагматическая составляющая. Автотест и make_dump.sh дают воспроизводимые "
        "артефакты для демонстрации: публичные данные читаются из snapshot, "
        "секреты — нет (в store); удаление очищает логическое хранилище. Для "
        "усиления защиты рекомендуется минимизировать lifetime plaintext, "
        "не держать ключ рядом с данными дольше необходимого и снимать core "
        "на Linux VM с gcore для более глубокого анализа остатков в heap."
    )

    pdf.h1("Список использованных источников")
    for i, s in enumerate(
        [
            "Ховард, М. Защищённый код / М. Ховард, Д. Лебланк. – М. : Русская редакция, 2004. – 704 с.",
            "Ховард, М. 24 смертных греха компьютерной безопасности / М. Ховард, Д. Лебланк, Дж. Вьега. – СПб. : Питер, 2010. – 400 с.",
            "Cryptography Fernet [Электронный ресурс]. – Режим доступа: https://cryptography.io/en/latest/fernet/.",
            "Apple Developer Documentation — vmmap [Электронный ресурс].",
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
