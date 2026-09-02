"""
PSIIZ Lab 2.1 — намеренно уязвимое веб-приложение (OWASP Top 10 2021).

Содержит CRUD пользователей, публичных и конфиденциальных заметок.
Уязвимости оставлены специально для анализа (2.1) и эксплуатации (2.2).
НЕ использовать в production.
"""

from __future__ import annotations

import html
import json
import os
import pickle
import sqlite3
import urllib.request
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", APP_DIR / "data" / "app.db"))

# A05: секрет в коде, DEBUG включён
app = Flask(__name__)
app.secret_key = "super-secret-hardcoded-key-12345"
app.config["DEBUG"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = False  # A07: cookie читается JS
app.config["SESSION_COOKIE_SECURE"] = False


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        );
        CREATE TABLE IF NOT EXISTS public_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            FOREIGN KEY(author_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS confidential_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            FOREIGN KEY(owner_id) REFERENCES users(id)
        );
        """
    )
    cur = db.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        # A02: пароли в открытом виде
        users = [
            ("admin", "admin", "admin"),
            ("alice", "alice", "user"),
            ("bob", "bob123", "user"),
            ("guest", "guest", "guest"),
        ]
        db.executemany(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            users,
        )
        db.execute(
            "INSERT INTO public_notes (author_id, title, body) VALUES (1, ?, ?)",
            ("Welcome", "Публичная заметка для всех"),
        )
        db.execute(
            "INSERT INTO confidential_notes (owner_id, title, body) VALUES (1, ?, ?)",
            ("Admin secret", "SSN: 123-45-6789; card: 4111111111111111"),
        )
        db.execute(
            "INSERT INTO confidential_notes (owner_id, title, body) VALUES (2, ?, ?)",
            ("Alice private", "Пароль от почты: Summer2020!"),
        )
        db.commit()
    db.close()


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Нужна авторизация")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


BASE = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>VulnNotes — Lab 2.1</title>
  <style>
    body{font-family:system-ui,sans-serif;max-width:960px;margin:24px auto;padding:0 16px}
    nav a{margin-right:12px}
    .card{border:1px solid #ddd;padding:12px;margin:8px 0;border-radius:8px}
    .err{color:#b00020} .ok{color:#0a7} .warn{background:#fff3cd;padding:8px;border-radius:6px}
    input,textarea,button{margin:4px 0;padding:6px}
    table{border-collapse:collapse;width:100%} td,th{border:1px solid #ccc;padding:6px}
  </style>
</head>
<body>
  <nav>
    <a href="/">Home</a>
    <a href="/public">Public notes</a>
    <a href="/confidential">Confidential</a>
    <a href="/search">Search</a>
    <a href="/vulns">OWASP map</a>
    {% if user %}
      <span>Hi, {{ user['username'] }} ({{ user['role'] }})</span>
      <a href="/logout">Logout</a>
    {% else %}
      <a href="/login">Login</a>
      <a href="/register">Register</a>
    {% endif %}
  </nav>
  <hr>
  {% for m in get_flashed_messages() %}<p class="ok">{{ m }}</p>{% endfor %}
  {{ body|safe }}
</body>
</html>
"""


def page(body: str):
    return render_template_string(BASE, body=body, user=current_user())


@app.route("/")
def index():
    body = """
    <h1>VulnNotes</h1>
    <p class="warn">Учебное приложение с OWASP Top 10 уязвимостями. Не для production.</p>
    <ul>
      <li>Регистрация / логин / logout</li>
      <li>CRUD публичных заметок</li>
      <li>CRUD конфиденциальных заметок</li>
      <li>Поиск</li>
    </ul>
    <p>Сид: admin/admin, alice/alice, bob/bob123, guest/guest</p>
    """
    return page(body)


# ---------- Auth ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")  # A07: нет политики паролей
        # A03: string format / no parameterized insert in spirit of weak code path
        # (здесь параметризовано для регистрации, SQLi в search)
        try:
            get_db().execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, 'user')",
                (username, password),
            )
            get_db().commit()
            flash("Пользователь создан")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return page("<p class='err'>Имя занято</p>" + register_form())
    return page(register_form())


def register_form() -> str:
    return """
    <h2>Register</h2>
    <form method="post">
      <div><input name="username" placeholder="username" required></div>
      <div><input name="password" type="password" placeholder="password" required></div>
      <button>Create</button>
    </form>
    """


@app.route("/login", methods=["GET", "POST"])
def login():
    # A04 / A07 / A09: нет rate limit, нет лога неудачных попыток
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # A03: SQL Injection в логине
        q = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        user = get_db().execute(q).fetchone()
        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("Вход выполнен")
            return redirect(url_for("index"))
        return page("<p class='err'>Неверный логин или пароль</p>" + login_form())
    return page(login_form())


def login_form() -> str:
    return """
    <h2>Login</h2>
    <form method="post">
      <div><input name="username" placeholder="username"></div>
      <div><input name="password" type="password" placeholder="password"></div>
      <button>Sign in</button>
    </form>
    <p>Hint for 2.2: SQLi в username/password, brute force без лимита.</p>
    """


@app.route("/logout")
def logout():
    session.clear()
    flash("Выход выполнен")
    return redirect(url_for("index"))


# ---------- Public notes ----------
@app.route("/public")
@login_required
def public_list():
    rows = get_db().execute(
        "SELECT n.*, u.username FROM public_notes n JOIN users u ON u.id = n.author_id"
    ).fetchall()
    items = "".join(
        f"<div class='card'><b>#{r['id']} {r['title']}</b> by {r['username']}"
        f"<pre>{r['body']}</pre>"
        f"<a href='/public/{r['id']}/edit'>edit</a> | "
        f"<a href='/public/{r['id']}/delete'>delete</a></div>"
        for r in rows
    )
    body = f"""
    <h2>Public notes</h2>
    <form method="post" action="/public/create">
      <input name="title" placeholder="title" required>
      <textarea name="body" placeholder="body" required></textarea>
      <button>Create</button>
    </form>
    {items}
    """
    return page(body)


@app.route("/public/create", methods=["POST"])
@login_required
def public_create():
    user = current_user()
    get_db().execute(
        "INSERT INTO public_notes (author_id, title, body) VALUES (?, ?, ?)",
        (user["id"], request.form["title"], request.form["body"]),
    )
    get_db().commit()
    return redirect(url_for("public_list"))


@app.route("/public/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def public_edit(note_id: int):
    db = get_db()
    note = db.execute("SELECT * FROM public_notes WHERE id = ?", (note_id,)).fetchone()
    if not note:
        return page("<p class='err'>Not found</p>")
    # A01: любой авторизованный может править чужие публичные
    if request.method == "POST":
        db.execute(
            "UPDATE public_notes SET title = ?, body = ? WHERE id = ?",
            (request.form["title"], request.form["body"], note_id),
        )
        db.commit()
        return redirect(url_for("public_list"))
    return page(
        f"""
        <h2>Edit public #{note_id}</h2>
        <form method="post">
          <input name="title" value="{note['title']}">
          <textarea name="body">{note['body']}</textarea>
          <button>Save</button>
        </form>
        """
    )


@app.route("/public/<int:note_id>/delete")
@login_required
def public_delete(note_id: int):
    # A01: нет проверки владельца
    get_db().execute("DELETE FROM public_notes WHERE id = ?", (note_id,))
    get_db().commit()
    return redirect(url_for("public_list"))


# ---------- Confidential notes ----------
@app.route("/confidential")
@login_required
def confidential_list():
    user = current_user()
    # показываем «свои», но IDOR ниже позволяет читать чужие
    rows = get_db().execute(
        "SELECT * FROM confidential_notes WHERE owner_id = ?",
        (user["id"],),
    ).fetchall()
    items = "".join(
        f"<div class='card'><b>#{r['id']} {r['title']}</b>"
        f"<pre>{r['body']}</pre>"
        f"<a href='/confidential/{r['id']}'>open</a> | "
        f"<a href='/confidential/{r['id']}/edit'>edit</a> | "
        f"<a href='/confidential/{r['id']}/delete'>delete</a></div>"
        for r in rows
    )
    body = f"""
    <h2>Confidential notes</h2>
    <form method="post" action="/confidential/create">
      <input name="title" placeholder="title" required>
      <textarea name="body" placeholder="body" required></textarea>
      <button>Create</button>
    </form>
    {items}
    <p>IDOR: попробуй /confidential/1 будучи alice</p>
    """
    return page(body)


@app.route("/confidential/create", methods=["POST"])
@login_required
def confidential_create():
    user = current_user()
    get_db().execute(
        "INSERT INTO confidential_notes (owner_id, title, body) VALUES (?, ?, ?)",
        (user["id"], request.form["title"], request.form["body"]),
    )
    get_db().commit()
    return redirect(url_for("confidential_list"))


@app.route("/confidential/<int:note_id>")
@login_required
def confidential_view(note_id: int):
    # A01 Broken Access Control — IDOR, нет проверки owner_id
    note = get_db().execute(
        "SELECT * FROM confidential_notes WHERE id = ?",
        (note_id,),
    ).fetchone()
    if not note:
        return page("<p class='err'>Not found</p>")
    return page(
        f"<h2>Confidential #{note['id']}</h2>"
        f"<p>owner_id={note['owner_id']}</p>"
        f"<h3>{note['title']}</h3><pre>{note['body']}</pre>"
    )


@app.route("/confidential/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def confidential_edit(note_id: int):
    db = get_db()
    note = db.execute("SELECT * FROM confidential_notes WHERE id = ?", (note_id,)).fetchone()
    if not note:
        return page("<p class='err'>Not found</p>")
    # A01: IDOR write
    if request.method == "POST":
        db.execute(
            "UPDATE confidential_notes SET title = ?, body = ? WHERE id = ?",
            (request.form["title"], request.form["body"], note_id),
        )
        db.commit()
        return redirect(url_for("confidential_list"))
    return page(
        f"""
        <h2>Edit confidential #{note_id}</h2>
        <form method="post">
          <input name="title" value="{note['title']}">
          <textarea name="body">{note['body']}</textarea>
          <button>Save</button>
        </form>
        """
    )


@app.route("/confidential/<int:note_id>/delete")
@login_required
def confidential_delete(note_id: int):
    # A01: IDOR delete
    get_db().execute("DELETE FROM confidential_notes WHERE id = ?", (note_id,))
    get_db().commit()
    return redirect(url_for("confidential_list"))


# ---------- Search: SQLi + XSS ----------
@app.route("/search")
@login_required
def search():
    q = request.args.get("q", "")
    rows = []
    if q:
        # A03: SQL Injection
        sql = (
            f"SELECT id, title, body, 'public' AS kind FROM public_notes "
            f"WHERE title LIKE '%{q}%' OR body LIKE '%{q}%' "
            f"UNION ALL "
            f"SELECT id, title, body, 'confidential' AS kind FROM confidential_notes "
            f"WHERE title LIKE '%{q}%' OR body LIKE '%{q}%'"
        )
        try:
            rows = get_db().execute(sql).fetchall()
        except Exception as e:
            # A05: утечка ошибок
            return page(f"<p class='err'>SQL error: {e}</p><pre>{sql}</pre>")

    # A03 XSS: отражение q без экранирования
    items = "".join(
        f"<div class='card'>[{r['kind']}] #{r['id']} <b>{r['title']}</b><pre>{r['body']}</pre></div>"
        for r in rows
    )
    # value экранируем, чтобы форма не ломалась; Query — без экрана (XSS)
    safe_q = html.escape(q, quote=True)
    body = f"""
    <h2>Search</h2>
    <form method="get">
      <input name="q" value="{safe_q}" style="width:70%">
      <button>Search</button>
    </form>
    <p><a href="/search?q=%3Cscript%3Edocument.write(%27%3Cpre+style%3Dbackground:%23fee;padding:12px;border:2px+solid+red%3E%3Cb%3EStolen+cookies:%3C/b%3E%3Cbr%3E%27%2Bdocument.cookie%2B%27%3C/pre%3E%27)%3C/script%3E">
      XSS demo: вывести cookies на экран</a></p>
    <p>Query: {q}</p>
    <div class="card" style="border-color:#c00">
      <b>Browser cookies (HttpOnly=False → JS читает session):</b>
      <pre id="cookie-dump" style="margin:8px 0 0;background:#1e1e1e;color:#0f0;padding:10px;white-space:pre-wrap;word-break:break-all;overflow-wrap:anywhere;max-width:100%"></pre>
    </div>
    <script>
      document.getElementById('cookie-dump').textContent = document.cookie || '(пусто)';
    </script>
    {items}
    """
    return page(body)


# ---------- A10 SSRF ----------
@app.route("/fetch", methods=["GET", "POST"])
@login_required
def fetch_url():
    result = ""
    if request.method == "POST":
        url = request.form.get("url", "")
        try:
            # A10: SSRF — нет allowlist, можно дергать internal/metadata
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = resp.read(4096).decode("utf-8", errors="replace")
            result = f"<h3>Response from {url}</h3><pre>{data}</pre>"
        except Exception as e:
            result = f"<p class='err'>{e}</p>"
    body = f"""
    <h2>URL Fetch (SSRF demo)</h2>
    <form method="post">
      <input name="url" placeholder="http://127.0.0.1:5000/" style="width:70%">
      <button>Fetch</button>
    </form>
    {result}
    """
    return page(body)


# ---------- A08 insecure deserialization ----------
@app.route("/import", methods=["GET", "POST"])
@login_required
def import_prefs():
    result = ""
    if request.method == "POST":
        raw = request.form.get("payload", "")
        try:
            # A08: pickle.loads от пользователя
            blob = bytes.fromhex(raw)
            obj = pickle.loads(blob)
            result = f"<pre>Imported: {obj!r}</pre>"
        except Exception as e:
            result = f"<p class='err'>{e}</p>"
    sample = pickle.dumps({"theme": "dark"}).hex()
    body = f"""
    <h2>Import prefs (pickle)</h2>
    <p>Вставь hex pickle-payload. Sample theme: <code>{sample}</code></p>
    <form method="post">
      <textarea name="payload" style="width:100%;height:80px"></textarea>
      <button>Import</button>
    </form>
    {result}
    """
    return page(body)


# ---------- A06 / debug info ----------
@app.route("/debug/config")
def debug_config():
    # A05: открытый debug endpoint
    return {
        "secret_key": app.secret_key,
        "debug": app.config["DEBUG"],
        "db_path": str(DB_PATH),
        "users_hint": "admin/admin, alice/alice",
    }


@app.route("/vulns")
def vulns():
    body = """
    <h2>OWASP Top 10:2025 — карта уязвимостей</h2>
    <p><a href="https://owasp.org/Top10/2025/" target="_blank">owasp.org/Top10/2025</a></p>
    <table>
      <tr><th>ID</th><th>Категория</th><th>Где в приложении</th></tr>
      <tr><td>A01</td><td>Broken Access Control</td><td>IDOR /confidential/&lt;id&gt;, /api/notes; SSRF /fetch</td></tr>
      <tr><td>A02</td><td>Security Misconfiguration</td><td>DEBUG=True, /debug/config, hardcode secret</td></tr>
      <tr><td>A03</td><td>Software Supply Chain Failures</td><td>старые deps без hashes (requirements.txt)</td></tr>
      <tr><td>A04</td><td>Cryptographic Failures</td><td>plaintext passwords, нет TLS</td></tr>
      <tr><td>A05</td><td>Injection</td><td>SQLi /login и /search; XSS /search?q=</td></tr>
      <tr><td>A06</td><td>Insecure Design</td><td>нет rate limit / MFA / политики паролей</td></tr>
      <tr><td>A07</td><td>Authentication Failures</td><td>слабые пароли, cookie без HttpOnly</td></tr>
      <tr><td>A08</td><td>Software or Data Integrity Failures</td><td>/import pickle.loads</td></tr>
      <tr><td>A09</td><td>Security Logging and Alerting Failures</td><td>failed login не пишется</td></tr>
      <tr><td>A10</td><td>Mishandling of Exceptional Conditions</td><td>SQL/exception text в ответе /search</td></tr>
    </table>
    <p><a href="/fetch">SSRF (A01)</a> · <a href="/import">Pickle (A08)</a> · <a href="/debug/config">Debug (A02)</a> · <a href="/search?q=%27">Bad SQL (A10)</a></p>
    """
    return page(body)


@app.route("/api/notes/<int:note_id>")
def api_note(note_id: int):
    # A01: API без авторизации отдаёт confidential
    note = get_db().execute(
        "SELECT * FROM confidential_notes WHERE id = ?",
        (note_id,),
    ).fetchone()
    if not note:
        return {"error": "not found"}, 404
    return dict(note)


if __name__ == "__main__":
    init_db()
    # A05: слушаем 0.0.0.0, debug
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
