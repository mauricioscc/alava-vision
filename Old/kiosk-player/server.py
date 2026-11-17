"""Servidor do painel ADM + API do Kiosk Player.

Uso:
    pip install -r requirements.txt
    ADMIN_PASSWORD=suasenha python server.py

Painel: http://IP-DO-SERVIDOR:8080/
"""
import json
import os
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

BASE = Path(__file__).parent
DATA_FILE = BASE / "data.json"
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")  # vazio = sem senha
PORT = int(os.environ.get("PORT", "8080"))

app = Flask(__name__)
lock = threading.Lock()


def load():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 0, "pages": []}


def save(data):
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DATA_FILE)


def authorized():
    if not ADMIN_PASSWORD:
        return True
    a = request.authorization
    return bool(a and a.username == ADMIN_USER and a.password == ADMIN_PASSWORD)


def deny():
    return Response("Acesso restrito", 401, {"WWW-Authenticate": 'Basic realm="Kiosk ADM"'})


@app.get("/")
def admin():
    if not authorized():
        return deny()
    return send_from_directory(BASE, "admin.html")


# O player lê sem senha (roda na mesma máquina/rede); só a escrita é protegida.
@app.get("/api/pages")
def get_pages():
    return jsonify(load())


@app.put("/api/pages")
def put_pages():
    if not authorized():
        return deny()
    body = request.get_json(force=True, silent=True) or {}
    pages = []
    for p in body.get("pages", []):
        url = str(p.get("url", "")).strip()
        if not url:
            continue
        if not url.lower().startswith(("http://", "https://", "file://")):
            url = "https://" + url
        try:
            seconds = max(3, int(p.get("seconds", 30)))
        except (TypeError, ValueError):
            seconds = 30
        pages.append({
            "id": p.get("id") or uuid.uuid4().hex[:8],
            "url": url,
            "seconds": seconds,
            "enabled": bool(p.get("enabled", True)),
        })
    with lock:
        data = {"version": int(time.time() * 1000), "pages": pages}
        save(data)
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
