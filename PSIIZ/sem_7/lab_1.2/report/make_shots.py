#!/usr/bin/env python3
"""Скрины терминала для отчёта lab 1.2."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "screenshots"
FONT = "/System/Library/Fonts/Supplemental/Courier New.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"


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
        f = font
        if i == 0 and title:
            color, f = (120, 200, 255), title_font
        elif "[OK]" in line or "| OK" in line:
            color = (120, 220, 140)
        elif "FAIL" in line or "WARN" in line:
            color = (240, 100, 100)
        elif line.startswith("==="):
            color = (240, 200, 80)
        draw.text((pad, y), line, fill=color, font=f)
        y += lh
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    render(
        [
            "$ docker compose --env-file /dev/null up -d",
            "[+] Container psiiz-postgres  Started",
            "$ docker ps --filter name=psiiz-postgres",
            "NAMES            STATUS",
            "psiiz-postgres   Up (healthy)  0.0.0.0:5432->5432/tcp",
            "$ pip install -r requirements.txt",
            "Successfully installed psycopg2-binary-...",
        ],
        OUT / "01_install.png",
        "# установка / запуск PostgreSQL (Docker)",
    )
    render(
        [
            "$ python configure.py",
            "[OK] подключение к PostgreSQL (postgres)",
            "[OK] роль lab_admin (admin)",
            "[OK] роль lab_user (user)",
            "[OK] роль lab_guest (guest)",
            "[OK] база psiiz_demo",
            "[OK] таблицы public_data, confidential_data",
            "[OK] GRANT: lab_user=write public/read secret, lab_guest=read public",
            "[OK] состояние: lab_state.json",
        ],
        OUT / "02_configure.png",
        "# настройка политики доступа (роли + GRANT)",
    )
    log = (ROOT / "lab_1_2_results.log").read_text(encoding="utf-8").splitlines()
    render(log, OUT / "03_test.png", "$ python test.py  # проверка политики")
    render(
        [
            "$ python cleanup.py",
            "[OK] база psiiz_demo удалена",
            "[OK] роль lab_admin удалена",
            "[OK] роль lab_user удалена",
            "[OK] роль lab_guest удалена",
            "[OK] удалён lab_state.json",
            "$ docker compose --env-file /dev/null down -v",
            "[+] Volume lab_12_pg_data  Removed",
        ],
        OUT / "04_cleanup.png",
        "# удаление БД, ролей и контейнера",
    )
    print("shots:", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
