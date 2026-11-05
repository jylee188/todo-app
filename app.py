import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

DB_PATH = Path(os.environ.get(
    "TODO_DB_PATH", str(Path(__file__).resolve().parent / "todo.db")
)).expanduser().resolve()

WEB_ORIGIN = os.environ.get("WEB_ORIGIN", "http://127.0.0.1:5500")

CORS(
    app,
    resources={r"/api/.*": {"origins": [WEB_ORIGIN]}},
    methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


def connect_db():
    return sqlite3.connect(DB_PATH, timeout=10)


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with closing(connect_db()) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER DEFAULT 0
            )
        """)
        conn.commit()


@app.get("/api/todos")
def get_todos():
    with closing(connect_db()) as conn:
        rows = conn.execute(
            "SELECT id, title, completed FROM todos ORDER BY id DESC"
        ).fetchall()

    return jsonify([
        {"id": row[0], "title": row[1], "completed": bool(row[2])}
        for row in rows
    ])


@app.post("/api/todos")
def add_todo():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON 객체를 보내주세요."}), 400

    title = data.get("title")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "할 일을 입력하세요."}), 400

    title = title.strip()

    if len(title) > 200:
        return jsonify({"error": "할 일은 200자 이하로 입력하세요."}), 400

    with closing(connect_db()) as conn:
        cursor = conn.execute(
            "INSERT INTO todos (title) VALUES (?)", (title,)
        )
        conn.commit()
        todo_id = cursor.lastrowid

    return jsonify({"success": True, "id": todo_id}), 201


@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    with closing(connect_db()) as conn:
        cursor = conn.execute(
            "DELETE FROM todos WHERE id = ?", (todo_id,)
        )
        conn.commit()
        deleted = cursor.rowcount

    if deleted == 0:
        return jsonify({"error": "할 일을 찾을 수 없습니다."}), 404

    return jsonify({"success": True})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)