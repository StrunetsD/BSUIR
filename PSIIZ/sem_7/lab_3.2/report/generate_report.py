#!/usr/bin/env python3
"""Отчёт lab 3.2 — методика и сравнение (без отдельного «эталонного» кода)."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "screenshots"
OUT = ROOT / "Отчет_ЛР3.2_Струнец_ДП_321701.pdf"

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
        "по лабораторной работе № 3 (часть 2)",
        "по дисциплине",
        "«Проектирование защищенных интеллектуальных",
        "информационных систем»",
    ):
        pdf.multi_cell(0, 7.5, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.body(14)
    pdf.multi_cell(
        0, 7.5,
        "Тема: Методика оценки безопасности кода (на основе lab 3.1)",
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
        "Цель работы — на основе результатов лабораторной работы № 3.1 "
        "сформулировать методику оценки безопасности кода, применить её к "
        "собственной реализации и выполнить сравнительный анализ с типовым "
        "(«предоставленным») подходом к той же задаче — хранению публичных и "
        "конфиденциальных данных в оперативной памяти."
    )

    pdf.h1("2 Описание алгоритмов")
    pdf.h2("2.1 Реализация лабораторной работы № 3.1")
    pdf.para(
        "Приложение In-Memory Secure Store (Python, Tkinter): CRUD записей в RAM. "
        "Публичные данные хранятся открытым текстом; конфиденциальные после ввода "
        "хешируются (PBKDF2-HMAC-SHA256) или шифруются (Fernet/AES). Реализованы "
        "валидация ввода, удаление с затиранием полей объекта, снимки памяти "
        "(make_dump.sh) и просмотр артефактов в UI. Подробный разбор и дампы "
        "приведены в отчёте по лабораторной работе № 3.1."
    )
    pdf.shot("04_own_protect.png", "Собственный код: защита данных (_protect)", 95)
    pdf.shot("05_own_ui.png", "Интерфейс приложения lab 3.1", 95)

    pdf.h2("2.2 Типовой предоставленный подход (для сравнения)")
    pdf.para(
        "Под «предоставленным алгоритмом» в рамках сравнения понимается "
        "распространённый учебный/черновой вариант той же постановки: те же "
        "операции create/update/delete в памяти, но без разделения обработки "
        "public и secret — значение (в том числе пароль или карта) записывается "
        "в структуру как plaintext; валидация отсутствует или минимальна; "
        "удаление сводится к удалению ссылки из коллекции без затирания; "
        "средства анализа RAM и метрик ресурсов не предусматриваются. "
        "Такой подход выбран как эталон антипаттернов, с которыми сопоставляется "
        "реализация 3.1 (отдельная кодовая база для сравнения не вводилась — "
        "разбор выполнен по критериям методики и наблюдениям из 3.1)."
    )

    pdf.h1("3 Анализ безопасности предоставленного подхода")
    pdf.para(
        "С точки зрения кода: конфиденциальность не обеспечивается — секрет в RAM "
        "неотличим от публичной строки. Нет гарантий на невалидный ввод. Ошибки "
        "часто проявляются необработанными исключениями. С точки зрения "
        "оперативной памяти: любой снимок/strings по процессу с высокой "
        "вероятностью содержит исходные секреты; после delete остатки plaintext "
        "в куче ещё более вероятны, так как нет даже явного затирания полей. "
        "Ключ шифрования отсутствует, потому что шифрования нет — атакующему "
        "достаточно чтения памяти."
    )

    pdf.h1("4 Описание созданной методики")
    pdf.para(
        "Методика содержит 10 критериев (оценка 0 / 1 / 2, максимум 20 баллов; "
        "порог «приемлемо для учебного стенда» — ≥ 14). Критерии сформированы "
        "по итогам 3.1:"
    )
    for t in (
        "разделение public и confidential;",
        "защита секрета при сохранении (хеш/шифр);",
        "валидация ввода;",
        "отсутствие plaintext секрета в store;",
        "логическое удаление и затирание полей;",
        "обработка ошибок без утечки внутренностей;",
        "ключ не захардкожен в репозитории;",
        "наличие инструментов снимков RAM;",
        "наблюдаемость CPU/RSS;",
        "документирование угроз (виджет, куча, ключ в процессе).",
    ):
        pdf.bullet(t)
    pdf.ln(1)
    pdf.para(
        "Корректность методики обосновывается тем, что она сочетает статический "
        "разбор кода и динамические признаки (маркеры в snapshot после "
        "create/update/delete), что прямо следует из задания 3.1 и закрывает "
        "требования 3.2 к сравнению вариантов."
    )
    pdf.shot("02_methodology.png", "Фрагмент методики (METHODOLOGY.md)", 100)

    pdf.h1("5 Сравнение по методике")
    pdf.para(
        "Ниже — качественное сравнение собственного варианта (3.1) с типовым "
        "предоставленным подходом по критериям методики."
    )
    pairs = [
        ("Разделение типов", "есть Kind public/hash/enc", "часто один тип хранения на всё"),
        ("Защита секрета", "PBKDF2 / Fernet сразу при записи", "plaintext в поле value"),
        ("Валидация", "проверки пустоты и длины", "обычно нет"),
        ("Store без plaintext секрета", "подтверждено маркерами в 3.1", "маркер секрета читается из RAM"),
        ("Удаление", "pop + затирание полей Record", "только удаление из коллекции"),
        ("Ошибки", "ValueError / диалоги UI", "сырые исключения"),
        ("Ключ", "генерация Fernet в runtime", "не применимо / отсутствует"),
        ("Дампы RAM", "make_dump.sh, DumpBrowser", "как правило не предусмотрены"),
        ("Ресурсы", "resources / getrusage / vmmap", "не измеряются"),
        ("Угрозы", "описаны в README и отчёте 3.1", "редко документируются"),
    ]
    for name, own, prov in pairs:
        pdf.bullet(f"{name}: свой вариант — {own}; предоставленный подход — {prov}.")
    pdf.ln(1)
    pdf.para(
        "Итог: реализация 3.1 удовлетворяет методике на высоком уровне (по сути "
        "закрывает все 10 критериев); типовой предоставленный подход не проходит "
        "ключевые пункты защиты секрета и анализа памяти. Методика позволяет "
        "применить ту же таблицу к любому коду, выданному преподавателем, без "
        "изменения шкалы критериев."
    )

    pdf.h1("6 Вывод")
    pdf.para(
        "Семантическая составляющая. Сформулирована методика оценки безопасности "
        "кода для приложений с данными в RAM; на её основе сопоставлены "
        "собственная реализация 3.1 и типовой незащищённый подход к той же задаче."
    )
    pdf.para(
        "Прагматическая составляющая. Чек-лист из 10 критериев можно повторно "
        "использовать при проверке чужого варианта (в том числе официально "
        "предоставленного на занятии): достаточно пройти критерии и зафиксировать "
        "доказательства из кода и снимков памяти, как это сделано в лабораторной "
        "работе № 3.1."
    )

    pdf.h1("Список использованных источников")
    for i, s in enumerate(
        [
            "Ховард, М. Защищённый код / М. Ховард, Д. Лебланк. – М. : Русская редакция, 2004. – 704 с.",
            "Ховард, М. 24 смертных греха компьютерной безопасности / М. Ховард, Д. Лебланк, Дж. Вьега. – СПб. : Питер, 2010. – 400 с.",
            "Отчёт по лабораторной работе № 3.1 (Струнец Д. П., 2026).",
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
