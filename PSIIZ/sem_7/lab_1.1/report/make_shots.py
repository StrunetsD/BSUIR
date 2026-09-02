#!/usr/bin/env python3
"""Терминальные «скрины» из лога lab_1_1 для отчёта."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "lab_1_1_results.log"
OUT = Path(__file__).resolve().parent / "screenshots"
ANSI = re.compile(r"\x1b\[[0-9;]*m")

FONT = "/System/Library/Fonts/Supplemental/Courier New.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"


def strip(s: str) -> str:
    return ANSI.sub("", s).rstrip("\n")


def render(lines: list[str], path: Path, title: str = "") -> None:
    font = ImageFont.truetype(FONT, 18)
    title_font = ImageFont.truetype(FONT_B, 18)
    pad, lh = 18, 22
    body = ([title] if title else []) + lines
    w = max(980, max(int(font.getlength(x)) for x in body) + 2 * pad)
    h = pad * 2 + lh * len(body)
    img = Image.new("RGB", (w, h), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    y = pad
    for i, line in enumerate(body):
        color = (200, 200, 200)
        if i == 0 and title:
            color = (120, 200, 255)
            f = title_font
        else:
            f = font
            if "[OK]" in line:
                color = (120, 220, 140)
            elif "[FAIL]" in line:
                color = (240, 100, 100)
            elif "[INFO]" in line or line.startswith("==="):
                color = (240, 200, 80)
            elif "YES" in line and "NO" not in line.split("|")[-1]:
                color = (180, 220, 180)
        draw.text((pad, y), line, fill=color, font=f)
        y += lh
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def main() -> None:
    raw = [strip(x) for x in LOG.read_text(encoding="utf-8", errors="replace").splitlines()]
    OUT.mkdir(parents=True, exist_ok=True)

    # создание пользователей/каталогов
    head = [x for x in raw if x][:35]
    render(head, OUT / "01_setup.png", "$ sudo ./lab_1_1.sh  # создание пользователей и каталогов")

    # дерево / права
    try:
        i0 = next(i for i, x in enumerate(raw) if x.startswith("--- tree ---"))
        tree = raw[i0 : i0 + 45]
    except StopIteration:
        tree = raw[40:80]
    render(tree, OUT / "02_tree.png", "$ ls -laR pzs  # фрагмент дерева и прав")

    # проверка доступа к файлам (фрагмент)
    files = [x for x in raw if x.startswith("FILE pzs11/file1")][:24]
    render(files or raw[100:130], OUT / "03_file_access.png", "# п.14 проверка read/write/exec (фрагмент pzs11)")

    # процессы
    procs = [x for x in raw if x.startswith("PROC ")][:18]
    render(procs or ["(нет PROC-строк)"], OUT / "04_proc_kill.png", "# п.15 остановка процессов file*5")

    # каталоги
    dirs = [x for x in raw if x.startswith("DIR ")]
    render(dirs, OUT / "05_dir_ops.png", "# п.16 операции list/create/delete по каталогам")

    # cleanup
    tail = [x for x in raw if x][-20:]
    render(tail, OUT / "06_cleanup.png", "# п.17 удаление объектов")

    print("shots:", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
