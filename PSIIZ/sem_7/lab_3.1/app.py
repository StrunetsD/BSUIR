#!/usr/bin/env python3
"""
Lab 3.1 — интерактивное хранилище в оперативной памяти.

Публичные записи хранятся как есть.
Конфиденциальные — сразу хешируются (PBKDF2) или шифруются (Fernet).
"""

from __future__ import annotations

import hashlib
import os
import secrets
import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Optional

APP_DIR = Path(__file__).resolve().parent
DUMP_SCRIPT = APP_DIR / "make_dump.sh"
DUMPS_DIR = APP_DIR / "dumps"
try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore


class Kind(str, Enum):
    PUBLIC = "public"
    CONFIDENTIAL_HASH = "confidential_hash"
    CONFIDENTIAL_ENC = "confidential_enc"


@dataclass
class Record:
    id: int
    title: str
    kind: Kind
    # то, что реально лежит в RAM после обработки
    stored: str
    # только для шифрованных — можно расшифровать ключом приложения
    salt_hex: str = ""
    note: str = ""


@dataclass
class MemoryStore:
    """Все данные живут только в оперативной памяти процесса."""

    _items: dict[int, Record] = field(default_factory=dict)
    _next_id: int = 1
    master_key: bytes = field(default_factory=bytes)
    _fernet: object = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if Fernet is None:
            self.master_key = secrets.token_bytes(32)
            self._fernet = None
        else:
            if not self.master_key:
                self.master_key = Fernet.generate_key()
            self._fernet = Fernet(self.master_key)

    def list_records(self) -> list[Record]:
        return [self._items[i] for i in sorted(self._items)]

    def get(self, record_id: int) -> Optional[Record]:
        return self._items.get(record_id)

    def create(self, title: str, raw_value: str, kind: Kind) -> Record:
        title = title.strip()
        if not title:
            raise ValueError("Заголовок не может быть пустым.")
        if len(title) > 80:
            raise ValueError("Заголовок слишком длинный (макс. 80 символов).")
        if not raw_value:
            raise ValueError("Значение не может быть пустым.")
        if len(raw_value) > 10_000:
            raise ValueError("Значение слишком длинное (макс. 10000 символов).")

        stored, salt, note = self._protect(raw_value, kind)
        rec = Record(
            id=self._next_id,
            title=title,
            kind=kind,
            stored=stored,
            salt_hex=salt,
            note=note,
        )
        self._items[rec.id] = rec
        self._next_id += 1
        # стараемся не оставлять plaintext в локальной переменной дольше нужного
        raw_value = ""
        return rec

    def update(self, record_id: int, title: str, raw_value: str) -> Record:
        rec = self._items.get(record_id)
        if rec is None:
            raise ValueError(f"Запись #{record_id} не найдена.")
        title = title.strip()
        if not title:
            raise ValueError("Заголовок не может быть пустым.")
        if not raw_value:
            raise ValueError("Новое значение не может быть пустым.")
        if len(raw_value) > 10_000:
            raise ValueError("Значение слишком длинное (макс. 10000 символов).")

        stored, salt, note = self._protect(raw_value, rec.kind)
        rec.title = title
        rec.stored = stored
        rec.salt_hex = salt
        rec.note = note
        raw_value = ""
        return rec

    def delete(self, record_id: int) -> None:
        rec = self._items.pop(record_id, None)
        if rec is None:
            raise ValueError(f"Запись #{record_id} не найдена.")
        # затираем поля (для демонстрации политики работы с памятью)
        rec.stored = "\x00" * len(rec.stored)
        rec.title = ""
        rec.salt_hex = ""
        rec.note = ""

    def reveal(self, record_id: int) -> str:
        """Показать расшифрованное значение (только для confidential_enc)."""
        rec = self._items.get(record_id)
        if rec is None:
            raise ValueError(f"Запись #{record_id} не найдена.")
        if rec.kind == Kind.PUBLIC:
            return rec.stored
        if rec.kind == Kind.CONFIDENTIAL_HASH:
            raise ValueError("Хеш необратим — исходное значение восстановить нельзя.")
        if self._fernet is None:
            raise ValueError("Нужен пакет cryptography: pip install cryptography")
        try:
            return self._fernet.decrypt(rec.stored.encode("ascii")).decode("utf-8")
        except InvalidToken as e:
            raise ValueError("Не удалось расшифровать запись.") from e

    def _protect(self, raw: str, kind: Kind) -> tuple[str, str, str]:
        if kind == Kind.PUBLIC:
            return raw, "", "хранится открытым текстом в RAM"
        if kind == Kind.CONFIDENTIAL_HASH:
            salt = secrets.token_bytes(16)
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                raw.encode("utf-8"),
                salt,
                120_000,
            )
            stored = digest.hex()
            return stored, salt.hex(), "PBKDF2-HMAC-SHA256 (необратимо)"
        if kind == Kind.CONFIDENTIAL_ENC:
            if self._fernet is None:
                raise ValueError(
                    "Для шифрования установите: pip install cryptography"
                )
            token = self._fernet.encrypt(raw.encode("utf-8")).decode("ascii")
            return token, "", "Fernet (AES) — обратимо ключом приложения"
        raise ValueError("Неизвестный тип записи")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Lab 3.1 — In-Memory Secure Store")
        self.geometry("920x560")
        self.minsize(800, 480)

        self.store = MemoryStore()
        self._selected_id: Optional[int] = None

        self._build()
        self.refresh()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(top, text="Записи в оперативной памяти", padding=8)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cols = ("id", "kind", "title", "stored")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=18)
        self.tree.heading("id", text="ID")
        self.tree.heading("kind", text="Тип")
        self.tree.heading("title", text="Заголовок")
        self.tree.heading("stored", text="Значение в RAM")
        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("kind", width=140)
        self.tree.column("title", width=140)
        self.tree.column("stored", width=280)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        right = ttk.LabelFrame(top, text="Создать / обновить", padding=10)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        ttk.Label(right, text="Заголовок").grid(row=0, column=0, sticky=tk.W)
        self.title_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.title_var, width=36).grid(row=1, column=0, pady=(0, 8))

        ttk.Label(right, text="Значение (plaintext только при вводе)").grid(
            row=2, column=0, sticky=tk.W
        )
        self.value_text = tk.Text(right, width=36, height=6)
        self.value_text.grid(row=3, column=0, pady=(0, 8))

        ttk.Label(right, text="Тип данных").grid(row=4, column=0, sticky=tk.W)
        self.kind_var = tk.StringVar(value=Kind.PUBLIC.value)
        kinds = [
            (Kind.PUBLIC.value, "Публичные (без защиты)"),
            (Kind.CONFIDENTIAL_HASH.value, "Конфиденциальные → хеш"),
            (Kind.CONFIDENTIAL_ENC.value, "Конфиденциальные → шифр"),
        ]
        kind_box = ttk.Combobox(
            right,
            textvariable=self.kind_var,
            values=[k[0] for k in kinds],
            state="readonly",
            width=34,
        )
        kind_box.grid(row=5, column=0, pady=(0, 4))
        self.kind_hint = ttk.Label(right, text=kinds[0][1], wraplength=260)
        self.kind_hint.grid(row=6, column=0, sticky=tk.W, pady=(0, 8))
        kind_box.bind("<<ComboboxSelected>>", self._on_kind)

        btns = ttk.Frame(right)
        btns.grid(row=7, column=0, sticky=tk.EW)
        ttk.Button(btns, text="Создать", command=self.on_create).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Обновить выбранную", command=self.on_update).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Удалить выбранную", command=self.on_delete).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="Показать / расшифровать", command=self.on_reveal).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(btns, text="Дамп RAM (make_dump.sh)", command=self.on_dump).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(btns, text="Снимки памяти…", command=self.on_open_dumps).pack(
            fill=tk.X, pady=2
        )
        ttk.Button(btns, text="Очистить форму", command=self.clear_form).pack(fill=tk.X, pady=2)

        bottom = ttk.Frame(self, padding=(10, 0, 10, 10))
        bottom.pack(fill=tk.X)
        self.status = ttk.Label(
            bottom,
            text="Данные только в RAM процесса. PID см. в заголовке статуса после старта.",
            wraplength=880,
        )
        self.status.pack(anchor=tk.W)
        self._set_status(f"Готово. PID={self._pid()} — удобно для дампа памяти (lab 3.1).")

    def _pid(self) -> int:
        return os.getpid()

    def _on_kind(self, _event=None) -> None:
        labels = {
            Kind.PUBLIC.value: "Публичные (без защиты)",
            Kind.CONFIDENTIAL_HASH.value: "Конфиденциальные → хеш (PBKDF2, необратимо)",
            Kind.CONFIDENTIAL_ENC.value: "Конфиденциальные → шифр (Fernet, обратимо)",
        }
        self.kind_hint.configure(text=labels.get(self.kind_var.get(), ""))

    def _set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def _read_value(self) -> str:
        return self.value_text.get("1.0", tk.END).rstrip("\n")

    def clear_form(self) -> None:
        self.title_var.set("")
        self.value_text.delete("1.0", tk.END)
        self._selected_id = None
        self.tree.selection_remove(self.tree.selection())

    def refresh(self) -> None:
        for i in self.tree.get_children():
            self.tree.delete(i)
        kind_label = {
            Kind.PUBLIC: "public",
            Kind.CONFIDENTIAL_HASH: "secret→hash",
            Kind.CONFIDENTIAL_ENC: "secret→enc",
        }
        for rec in self.store.list_records():
            preview = rec.stored if len(rec.stored) <= 48 else rec.stored[:45] + "..."
            self.tree.insert(
                "",
                tk.END,
                iid=str(rec.id),
                values=(rec.id, kind_label[rec.kind], rec.title, preview),
            )

    def on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        self._selected_id = int(sel[0])
        rec = self.store.get(self._selected_id)
        if not rec:
            return
        self.title_var.set(rec.title)
        self.kind_var.set(rec.kind.value)
        self._on_kind()
        self.value_text.delete("1.0", tk.END)
        self.value_text.insert("1.0", "(введите НОВОЕ plaintext-значение для обновления)")
        self._set_status(
            f"Выбрана #{rec.id} [{rec.kind.value}]: в RAM лежит «{rec.stored[:64]}…» ({rec.note})"
            if len(rec.stored) > 64
            else f"Выбрана #{rec.id} [{rec.kind.value}]: в RAM лежит «{rec.stored}» ({rec.note})"
        )

    def on_create(self) -> None:
        try:
            kind = Kind(self.kind_var.get())
            rec = self.store.create(self.title_var.get(), self._read_value(), kind)
        except ValueError as e:
            messagebox.showerror("Валидация", str(e))
            return
        self.refresh()
        self.clear_form()
        self._set_status(
            f"Создана #{rec.id}. В памяти: {rec.stored[:80]}{'…' if len(rec.stored) > 80 else ''}"
        )

    def on_update(self) -> None:
        if self._selected_id is None:
            messagebox.showwarning("Обновление", "Сначала выберите запись в таблице.")
            return
        try:
            rec = self.store.update(
                self._selected_id, self.title_var.get(), self._read_value()
            )
        except ValueError as e:
            messagebox.showerror("Валидация", str(e))
            return
        self.refresh()
        self._set_status(f"Обновлена #{rec.id}. Новый stored-блок перезаписан в RAM.")

    def on_delete(self) -> None:
        if self._selected_id is None:
            messagebox.showwarning("Удаление", "Сначала выберите запись в таблице.")
            return
        rid = self._selected_id
        try:
            self.store.delete(rid)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return
        self.refresh()
        self.clear_form()
        self._set_status(
            f"Запись #{rid} удалена из словаря. Сделайте дамп памяти и проверьте остатки plaintext/хеша."
        )

    def on_reveal(self) -> None:
        if self._selected_id is None:
            messagebox.showwarning("Просмотр", "Сначала выберите запись.")
            return
        try:
            text = self.store.reveal(self._selected_id)
        except ValueError as e:
            messagebox.showinfo("Просмотр", str(e))
            return
        messagebox.showinfo("Расшифровано / публичное значение", text)

    def _write_store_snapshot(self) -> Path:
        DUMPS_DIR.mkdir(parents=True, exist_ok=True)
        path = DUMPS_DIR / "_last_store_snapshot.txt"
        lines = [
            f"pid={self._pid()}",
            f"records={len(self.store.list_records())}",
            "",
        ]
        for rec in self.store.list_records():
            lines.append(
                f"#{rec.id}\tkind={rec.kind.value}\ttitle={rec.title}\t"
                f"salt={rec.salt_hex}\tstored={rec.stored}"
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def on_dump(self) -> None:
        if not DUMP_SCRIPT.is_file():
            messagebox.showerror("Дамп", f"Не найден скрипт:\n{DUMP_SCRIPT}")
            return

        label = simpledialog.askstring(
            "Дамп RAM",
            "Метка дампа (after_create / after_update / after_delete / manual):",
            initialvalue="manual",
            parent=self,
        )
        if not label:
            return
        label = label.strip().replace(" ", "_")

        snap = self._write_store_snapshot()
        env = os.environ.copy()
        env["DUMP_DIR"] = str(DUMPS_DIR)

        try:
            # на всякий случай выставляем +x
            DUMP_SCRIPT.chmod(DUMP_SCRIPT.stat().st_mode | 0o111)
            proc = subprocess.run(
                ["/bin/bash", str(DUMP_SCRIPT), str(self._pid()), label],
                cwd=str(APP_DIR),
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired:
            messagebox.showerror("Дамп", "Таймаут выполнения make_dump.sh")
            return
        except OSError as e:
            messagebox.showerror("Дамп", str(e))
            return

        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        # последняя строка stdout — путь OUT
        out_dir = out.splitlines()[-1] if out else ""
        summary = (
            f"exit={proc.returncode}\n"
            f"snapshot={snap}\n"
            f"out_dir={out_dir}\n\n"
            f"--- stdout ---\n{out[-2000:]}\n\n"
            f"--- stderr ---\n{err[-1500:]}"
        )
        if proc.returncode == 0:
            self._set_status(f"Дамп сохранён: {out_dir}")
            messagebox.showinfo("Дамп RAM", summary)
            self.on_open_dumps(select_dir=out_dir)
        else:
            self._set_status("Дамп завершился с ошибкой — см. сообщение")
            messagebox.showerror("Дамп RAM", summary)

    def on_open_dumps(self, select_dir: str | Path | None = None) -> None:
        DumpBrowser(self, select_name=Path(select_dir).name if select_dir else None)


class DumpBrowser(tk.Toplevel):
    """Просмотр каталога dumps/ без терминала."""

    TEXT_FILES = {
        "RESULT.txt",
        "meta.txt",
        "store_snapshot.txt",
        "resources.txt",
        "vmmap.txt",
        "maps.txt",
        "ps.txt",
        "strings_head.txt",
        "core_size.txt",
        "lldb.out",
        "lldb.err",
        "gcore.out",
        "gcore.err",
        "gdb.out",
        "gdb.err",
        "vmmap.err",
    }
    MAX_CHARS = 400_000

    def __init__(self, master: App, select_name: str | None = None) -> None:
        super().__init__(master)
        self.title("Снимки / дампы памяти — lab_3.1/dumps")
        self.geometry("980x620")
        self.minsize(800, 480)
        self._app = master
        self._dump_dirs: list[Path] = []

        root = ttk.Frame(self, padding=8)
        root.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(root)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Снимки").pack(anchor=tk.W)
        self.dump_list = tk.Listbox(left, width=42, height=18, exportselection=False)
        self.dump_list.pack(fill=tk.BOTH, expand=True)
        self.dump_list.bind("<<ListboxSelect>>", self._on_dump_select)

        ttk.Label(left, text="Файлы снимка").pack(anchor=tk.W, pady=(8, 0))
        self.file_list = tk.Listbox(left, width=42, height=10, exportselection=False)
        self.file_list.pack(fill=tk.BOTH, expand=True)
        self.file_list.bind("<<ListboxSelect>>", self._on_file_select)

        btns = ttk.Frame(left)
        btns.pack(fill=tk.X, pady=6)
        ttk.Button(btns, text="Обновить список", command=self.refresh_dumps).pack(
            fill=tk.X, pady=1
        )
        ttk.Button(btns, text="Открыть папку dumps", command=self.open_dumps_folder).pack(
            fill=tk.X, pady=1
        )
        ttk.Button(
            btns, text="strings по core (если есть)", command=self.run_strings_core
        ).pack(fill=tk.X, pady=1)

        right = ttk.Frame(root)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        search_row = ttk.Frame(right)
        search_row.pack(fill=tk.X)
        ttk.Label(search_row, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        ttk.Entry(search_row, textvariable=self.search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=4
        )
        ttk.Button(search_row, text="Искать в снимке", command=self.search_in_dump).pack(
            side=tk.LEFT
        )

        self.view = tk.Text(right, wrap=tk.NONE, font=("Menlo", 11))
        yscroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.view.yview)
        xscroll = ttk.Scrollbar(right, orient=tk.HORIZONTAL, command=self.view.xview)
        self.view.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.view.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.status = ttk.Label(self, text=str(DUMPS_DIR), anchor=tk.W)
        self.status.pack(fill=tk.X, padx=8, pady=4)

        self.refresh_dumps(select_name=select_name)

    def _current_dump(self) -> Path | None:
        sel = self.dump_list.curselection()
        if not sel:
            return None
        return self._dump_dirs[sel[0]]

    def refresh_dumps(self, select_name: str | None = None) -> None:
        DUMPS_DIR.mkdir(parents=True, exist_ok=True)
        self.dump_list.delete(0, tk.END)
        self._dump_dirs = sorted(
            [p for p in DUMPS_DIR.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for p in self._dump_dirs:
            marker = ""
            if (p / "core").exists():
                marker = " [core]"
            elif (p / "store_snapshot.txt").exists():
                marker = " [snapshot]"
            self.dump_list.insert(tk.END, f"{p.name}{marker}")

        if not self._dump_dirs:
            self._show(
                "Папка dumps/ пуста.\n"
                "Сначала нажми «Дамп RAM (make_dump.sh)» в главном окне "
                "(метки: after_create / after_update / after_delete)."
            )
            return

        idx = 0
        if select_name:
            for i, p in enumerate(self._dump_dirs):
                if p.name == select_name:
                    idx = i
                    break
        self.dump_list.selection_clear(0, tk.END)
        self.dump_list.selection_set(idx)
        self.dump_list.see(idx)
        self._on_dump_select()

    def _on_dump_select(self, _event=None) -> None:
        dump = self._current_dump()
        self.file_list.delete(0, tk.END)
        if not dump:
            return
        files = sorted(dump.iterdir(), key=lambda p: p.name.lower())
        for f in files:
            if f.is_file():
                size = f.stat().st_size
                self.file_list.insert(tk.END, f"{f.name}  ({size} B)")
        # автопоказ RESULT или meta
        for prefer in ("RESULT.txt", "store_snapshot.txt", "meta.txt"):
            for i, f in enumerate(files):
                if f.is_file() and f.name == prefer:
                    self.file_list.selection_set(i)
                    self._load_file(f)
                    self.status.configure(text=str(dump))
                    return
        self.status.configure(text=str(dump))
        self._show(f"Снимок: {dump}\nВыбери файл слева.")

    def _on_file_select(self, _event=None) -> None:
        dump = self._current_dump()
        sel = self.file_list.curselection()
        if not dump or not sel:
            return
        name = self.file_list.get(sel[0]).split("  (")[0]
        path = dump / name
        if path.is_file():
            self._load_file(path)

    def _show(self, text: str) -> None:
        self.view.delete("1.0", tk.END)
        self.view.insert("1.0", text)

    def _load_file(self, path: Path) -> None:
        if path.name == "core" or path.suffix in {".core"} or path.stat().st_size > 5_000_000:
            if path.name == "core" or "core" in path.name:
                self._show(
                    f"Бинарный core: {path}\n"
                    f"Размер: {path.stat().st_size} байт\n\n"
                    "Нажми «strings по core» чтобы извлечь читаемые строки в UI.\n"
                    "Или выбери strings_head.txt, если он уже создан скриптом."
                )
                return
        try:
            raw = path.read_bytes()
        except OSError as e:
            self._show(str(e))
            return
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
        if len(text) > self.MAX_CHARS:
            text = text[: self.MAX_CHARS] + f"\n\n… обрезано, всего {len(text)} символов"
        self._show(text)
        self.status.configure(text=str(path))

    def search_in_dump(self) -> None:
        dump = self._current_dump()
        needle = self.search_var.get().strip()
        if not dump:
            messagebox.showwarning("Поиск", "Выбери снимок слева.")
            return
        if not needle:
            messagebox.showwarning("Поиск", "Введи строку для поиска (например SECRET_PLAIN).")
            return

        hits: list[str] = []
        for path in sorted(dump.iterdir()):
            if not path.is_file():
                continue
            if path.name == "core" or path.stat().st_size > 20_000_000:
                continue
            try:
                data = path.read_bytes()
            except OSError:
                continue
            try:
                text = data.decode("utf-8", errors="replace")
            except Exception:
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if needle in line:
                    hits.append(f"{path.name}:{n}: {line[:200]}")
                    if len(hits) >= 200:
                        break
            if len(hits) >= 200:
                break

        # если есть core — strings и фильтр в Python (без shell)
        core = dump / "core"
        if core.is_file() and len(hits) < 200:
            try:
                proc = subprocess.run(
                    ["strings", "-a", str(core)],
                    capture_output=True,
                    text=True,
                    timeout=90,
                    check=False,
                )
                for line in (proc.stdout or "").splitlines():
                    if needle in line:
                        hits.append(f"core/strings: {line[:200]}")
                        if len(hits) >= 200:
                            break
            except (OSError, subprocess.TimeoutExpired) as e:
                hits.append(f"(strings error: {e})")

        if not hits:
            self._show(f"Ничего не найдено для «{needle}» в {dump.name}")
        else:
            self._show(f"Поиск «{needle}» — {len(hits)} совп.\n\n" + "\n".join(hits))
        self.status.configure(text=f"Поиск в {dump}")

    def run_strings_core(self) -> None:
        dump = self._current_dump()
        if not dump:
            return
        core = dump / "core"
        if not core.is_file():
            messagebox.showinfo(
                "strings",
                "Файл core отсутствует в этом снимке.\n"
                "На macOS нужен sudo/права отладчика при создании дампа.\n"
                "Смотри store_snapshot.txt / vmmap.txt / RESULT.txt.",
            )
            # всё равно покажем текстовые артефакты
            snap = dump / "store_snapshot.txt"
            if snap.is_file():
                self._load_file(snap)
            return
        out_path = dump / "strings_head.txt"
        try:
            proc = subprocess.run(
                ["strings", "-a", str(core)],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            text = proc.stdout or ""
            # ограничиваем сохранение
            lines = text.splitlines()[:8000]
            out_path.write_text("\n".join(lines) + "\n", encoding="utf-8", errors="replace")
            self._show("\n".join(lines[:2000]) + ("\n…" if len(lines) > 2000 else ""))
            self.refresh_dumps(select_name=dump.name)
            self.status.configure(text=f"strings → {out_path}")
        except (OSError, subprocess.TimeoutExpired) as e:
            messagebox.showerror("strings", str(e))

    def open_dumps_folder(self) -> None:
        DUMPS_DIR.mkdir(parents=True, exist_ok=True)
        dump = self._current_dump() or DUMPS_DIR
        target = dump if dump.is_dir() else DUMPS_DIR
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(target)], check=False)
            elif sys.platform.startswith("linux"):
                subprocess.run(["xdg-open", str(target)], check=False)
            else:
                os.startfile(str(target))  # type: ignore[attr-defined]
        except OSError as e:
            messagebox.showerror("Папка", str(e))


def main() -> None:
    if Fernet is None:
        # GUI всё равно поднимем: хеш и public работают; enc покажет ошибку
        print("Подсказка: pip install cryptography  — для режима шифрования Fernet")
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
