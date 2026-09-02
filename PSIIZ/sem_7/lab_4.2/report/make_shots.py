#!/usr/bin/env python3
"""Терминальные скрины для отчёта lab 4.2."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "screenshots"
FONT = "/System/Library/Fonts/Supplemental/Courier New.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"


def render(lines: list[str], path: Path, title: str = "") -> None:
    font = ImageFont.truetype(FONT, 16)
    title_font = ImageFont.truetype(FONT_B, 16)
    pad, lh = 16, 20
    body = ([title] if title else []) + list(lines)
    wrapped: list[str] = []
    for line in body:
        line = line.replace("\t", "  ").rstrip()
        while len(line) > 118:
            wrapped.append(line[:118])
            line = line[118:]
        wrapped.append(line)
    body = wrapped[:58]
    w = min(1120, max(920, max(int(font.getlength(x)) for x in body) + 2 * pad))
    h = pad * 2 + lh * len(body)
    img = Image.new("RGB", (w, h), (28, 28, 28))
    draw = ImageDraw.Draw(img)
    y = pad
    for i, line in enumerate(body):
        f = title_font if (title and i == 0) else font
        color = (120, 200, 255) if (title and i == 0) else (220, 220, 220)
        draw.text((pad, y), line, font=f, fill=color)
        y += lh
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    print("wrote", path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8").splitlines()
    render(
        ["$ cat docker-compose.yml"] + compose[:45],
        OUT / "01_compose.png",
        "lab_4.2 — docker-compose (server + Suricata)",
    )

    rules = (ROOT / "suricata/rules/lab42.rules").read_text(encoding="utf-8").splitlines()
    render(
        ["$ cat suricata/rules/lab42.rules"] + rules,
        OUT / "02_rules.png",
        "Учебные правила Suricata (lab42.rules)",
    )

    before = (ROOT / "logs/before/summary.txt").read_text(encoding="utf-8").splitlines()
    render(
        ["$ ./scripts/snapshot_before.sh"] + before[:35],
        OUT / "03_before.png",
        "Снимок ДО: nginx/auth без алертов IDS",
    )

    after = (ROOT / "logs/after/summary.txt").read_text(encoding="utf-8").splitlines()
    # keep signature block + auth
    keep: list[str] = []
    for line in after:
        keep.append(line)
        if len(keep) > 55:
            break
    # Prefer a compact view: header + eve summary + auth
    compact = []
    for line in after:
        if line.startswith("===") or "fast_alerts" in line or "alert_events" in line:
            compact.append(line)
        elif line.startswith("     ") and "LAB42" in line:
            compact.append(line)
        elif line.startswith("top src") or (line.strip().startswith(("85", "7 ")) and "172." in line or "151." in line):
            compact.append(line)
        elif "auth Failed" in line or line.strip().isdigit():
            compact.append(line)
        elif line.startswith("--- eve") or line.startswith("--- nginx") or line.startswith("--- auth"):
            compact.append(line)
    if len(compact) < 12:
        compact = after[:40]
    render(
        ["$ ./scripts/analyze_suricata.sh"] + compact[:45],
        OUT / "04_after_alerts.png",
        "ПОСЛЕ: алерты Suricata (eve.json / fast.log)",
    )

    fast = (ROOT / "logs/suricata/fast.log").read_text(encoding="utf-8").splitlines()
    sample = fast[:8] + ["..."] + fast[-12:]
    render(
        ["$ tail logs/suricata/fast.log"] + sample,
        OUT / "05_fast_log.png",
        "Фрагмент fast.log",
    )

    deny = (ROOT / "logs/after/deny_ips.txt").read_text(encoding="utf-8").splitlines()
    render(
        [
            "$ ./scripts/ips_response_demo.sh",
            "Wrote IPs to logs/after/deny_ips.txt",
            *[f"  would block {x}" for x in deny if x.strip()],
            "",
            "Пример IPS на сервере:",
            "  iptables -A INPUT -s <IP> -j DROP",
            "  # или fail2ban-client set sshd banip <IP>",
        ],
        OUT / "06_ips_demo.png",
        "IPS-ответ: список IP для блокировки",
    )

    ps = [
        "NAMES                  STATUS",
        "psiiz-lab42-server     Up",
        "psiiz-lab42-suricata   Up",
        "",
        "$ docker logs psiiz-lab42-suricata | tail -3",
        "i: suricata: This is Suricata version 7.0.3 RELEASE running in SYSTEM mode",
        "i: threads: Threads created -> W: 10 FM: 1 FR: 1   Engine started.",
        "",
        "$ curl -sS -o /dev/null -w '%{http_code}\\n' http://localhost:8081/",
        "200",
    ]
    render(ps, OUT / "07_running.png", "Демонстрация работы стенда")


if __name__ == "__main__":
    main()
