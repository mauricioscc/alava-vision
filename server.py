"""
Alava Vision — Servidor (server.py) · versão 0.4.0

COMO RODAR
    pip install -r requirements.txt
    python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload
    Painel ........ http://localhost:8080/   (usuário "admin", senha = ADMIN_PASSWORD do .env)
    Testes rápidos no navegador:
        http://localhost:8080/api/player/state  → o que o player deve exibir AGORA (resultado da grade)
        http://localhost:8080/api/schedule      → blocos salvos na timeline
        http://localhost:8080/api/weather       → dados de clima usados na tela de previsão

COMO REVERTER
    Com Git (a partir da 0.3.0):  git log --oneline  e  git checkout <commit> -- server.py
    Para a 0.2.0 (antes do Git):
    1. Pare o servidor e o player (Ctrl+C).
    2. Copie os arquivos de backup_v0.2.0_20261117/ por cima dos atuais
       (server.py, player.py, static/index.html, static/weather.html).
    3. Opcional: copie também backup_v0.2.0_20261117/data/database.db* para data/.
       Sem esse passo o banco novo continua funcionando na versão antiga
       (as tabelas novas são apenas ignoradas).

MAPA DO CÓDIGO
    Configuração (.env) ............. constantes logo abaixo dos imports
    Banco e migração ................ db(), init_db()
    Autenticação .................... require_auth(), GET /api/ping
    Playlists ....................... GET/POST /api/playlists, PUT/DELETE /api/playlists/{id}
    Itens ........................... GET /api/playlist, POST /api/items,
                                      PUT /api/items/reorder, PUT/DELETE /api/items/{id}
    Grade horária (timeline) ........ GET/PUT /api/schedule, _clean_block()
    O que está no ar agora .......... resolve_now(), _pick_block(), GET /api/player/state
    Upload e arquivos ............... POST /api/upload, /uploads/* e /assets/* (StaticFiles)
    Configurações ................... load_settings(), GET/PUT /api/settings
    Clima ........................... _fetch_forecast(), _build_weather(), _inmet_alerts(), GET /api/weather
    Telas exibidas pelo player ...... /view/image/{id}, /view/video/{id}, /view/weather,
                                      /view/traffic, /view/message/{id}
"""
import json
import os
import secrets
import sqlite3
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

__version__ = "0.4.0"

load_dotenv()

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
ASSETS_DIR = BASE / "assets"
DB_PATH = DATA_DIR / "database.db"
STATIC_DIR = BASE / "static"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
PORT = int(os.getenv("PORT", "8080"))

WEATHER_LAT = os.getenv("WEATHER_LAT", "-23.5505")
WEATHER_LON = os.getenv("WEATHER_LON", "-46.6333")
WEATHER_CITY = os.getenv("WEATHER_CITY", "São Paulo")
MAPS_API_KEY = os.getenv("MAPS_API_KEY", "")
IBGE_CODE = os.getenv("IBGE_CODE", "")

ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
ALLOWED_VIDEO = {".mp4", ".webm", ".mov", ".avi"}

DEFAULT_PLAYLIST = "main"

app = FastAPI(title="Alava Vision", version=__version__)
security = HTTPBasic()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── Banco de dados ───────────────────────────────────────────────────────────

def db() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db():
    """Cria as tabelas e migra bancos da versão 0.2.0 sem perder dados.

    Na 0.2.0 existia uma única playlist (todos os registros de `items`).
    Agora cada item pertence a uma playlist; os itens antigos vão para a
    "Playlist padrão" (id 'main'), que também é a usada quando a grade
    horária está vazia — por isso o comportamento antigo continua igual.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id       TEXT PRIMARY KEY,
                type     TEXT NOT NULL,
                name     TEXT NOT NULL,
                config   TEXT DEFAULT '{}',
                duration INTEGER DEFAULT 30,
                active   INTEGER DEFAULT 1,
                ord      INTEGER DEFAULT 0,
                created_at INTEGER
            )""")
        cols = {r["name"] for r in con.execute("PRAGMA table_info(items)")}
        if "playlist_id" not in cols:
            con.execute(f"ALTER TABLE items ADD COLUMN playlist_id TEXT DEFAULT '{DEFAULT_PLAYLIST}'")
            con.execute("UPDATE items SET playlist_id=? WHERE playlist_id IS NULL", (DEFAULT_PLAYLIST,))
        con.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id         TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                created_at INTEGER
            )""")
        con.execute("INSERT OR IGNORE INTO playlists VALUES (?,?,?)",
                    (DEFAULT_PLAYLIST, "Playlist padrão", int(time.time())))
        # Grade horária: cada bloco aponta para uma playlist (trilha base)
        # ou para um item avulso (trilha de sobreposição). Minutos do dia: 0–1440.
        con.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id         TEXT PRIMARY KEY,
                kind       TEXT NOT NULL,
                ref_id     TEXT NOT NULL,
                start_min  INTEGER NOT NULL,
                end_min    INTEGER NOT NULL,
                created_at INTEGER
            )""")
        con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS version (id INTEGER PRIMARY KEY CHECK (id = 1), val INTEGER DEFAULT 0)")
        con.execute("INSERT OR IGNORE INTO version VALUES (1, 0)")
        con.commit()


def bump_version(con: sqlite3.Connection):
    """Marca que algo mudou; o player compara esse número e recarrega."""
    con.execute("UPDATE version SET val = ? WHERE id = 1", (int(time.time() * 1000),))


def item_dict(row: sqlite3.Row) -> dict:
    return dict(row) | {"config": json.loads(row["config"] or "{}")}


# ─── Autenticação ─────────────────────────────────────────────────────────────

def require_auth(creds: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(creds.username.encode(), ADMIN_USER.encode())
    ok_pass = secrets.compare_digest(creds.password.encode(), ADMIN_PASSWORD.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Acesso negado", headers={"WWW-Authenticate": "Basic"})
    return creds.username


@app.get("/api/ping", dependencies=[Depends(require_auth)])
def ping():
    return {"ok": True, "version": __version__}


# ─── Playlists ────────────────────────────────────────────────────────────────

@app.get("/api/playlists")
def list_playlists():
    with db() as con:
        rows = con.execute("""
            SELECT p.id, p.name, COUNT(i.id) AS item_count,
                   COALESCE(SUM(CASE WHEN i.active = 1 THEN i.duration END), 0) AS total_duration
            FROM playlists p LEFT JOIN items i ON i.playlist_id = p.id
            GROUP BY p.id ORDER BY (p.id != ?), p.created_at""", (DEFAULT_PLAYLIST,)).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/playlists", dependencies=[Depends(require_auth)])
async def create_playlist(request: Request):
    name = str((await request.json()).get("name", "")).strip() or "Nova playlist"
    pid = uuid.uuid4().hex[:12]
    with db() as con:
        con.execute("INSERT INTO playlists VALUES (?,?,?)", (pid, name, int(time.time())))
        con.commit()
    return {"id": pid, "name": name}


@app.put("/api/playlists/{pid}", dependencies=[Depends(require_auth)])
async def rename_playlist(pid: str, request: Request):
    name = str((await request.json()).get("name", "")).strip()
    if not name:
        raise HTTPException(400, "Informe um nome")
    with db() as con:
        if not con.execute("UPDATE playlists SET name=? WHERE id=?", (name, pid)).rowcount:
            raise HTTPException(404)
        bump_version(con)
        con.commit()
    return {"ok": True}


@app.delete("/api/playlists/{pid}", dependencies=[Depends(require_auth)])
def delete_playlist(pid: str):
    if pid == DEFAULT_PLAYLIST:
        raise HTTPException(400, "A playlist padrão não pode ser excluída")
    with db() as con:
        item_ids = [r["id"] for r in con.execute("SELECT id FROM items WHERE playlist_id=?", (pid,))]
        for iid in item_ids:
            con.execute("DELETE FROM schedule WHERE kind='item' AND ref_id=?", (iid,))
        con.execute("DELETE FROM items WHERE playlist_id=?", (pid,))
        con.execute("DELETE FROM schedule WHERE kind='playlist' AND ref_id=?", (pid,))
        con.execute("DELETE FROM playlists WHERE id=?", (pid,))
        bump_version(con)
        con.commit()
    return {"ok": True}


# ─── Itens ────────────────────────────────────────────────────────────────────

@app.get("/api/playlist")
def get_playlist(playlist_id: str | None = None):
    """Itens de uma playlist. Sem `playlist_id` devolve todos (compatível com a 0.2.0)."""
    with db() as con:
        if playlist_id:
            rows = con.execute("SELECT * FROM items WHERE playlist_id=? ORDER BY ord, created_at",
                               (playlist_id,)).fetchall()
        else:
            rows = con.execute("SELECT * FROM items ORDER BY ord, created_at").fetchall()
        ver = con.execute("SELECT val FROM version WHERE id=1").fetchone()
    return {"version": ver["val"] if ver else 0, "items": [item_dict(r) for r in rows]}


@app.post("/api/items", dependencies=[Depends(require_auth)])
async def add_item(request: Request):
    body = await request.json()
    with db() as con:
        pid = body.get("playlist_id") or DEFAULT_PLAYLIST
        if not con.execute("SELECT 1 FROM playlists WHERE id=?", (pid,)).fetchone():
            pid = DEFAULT_PLAYLIST
        max_ord = con.execute("SELECT COALESCE(MAX(ord),0) FROM items WHERE playlist_id=?", (pid,)).fetchone()[0]
        item_id = uuid.uuid4().hex[:12]
        con.execute(
            "INSERT INTO items (id,type,name,config,duration,active,ord,created_at,playlist_id) "
            "VALUES (?,?,?,?,?,1,?,?,?)",
            (item_id, body.get("type", "url"), body.get("name", "Sem nome"), json.dumps(body.get("config", {})),
             max(3, int(body.get("duration", 30))), max_ord + 1, int(time.time()), pid))
        bump_version(con)
        con.commit()
    return {"id": item_id}


# Declarada antes de /api/items/{item_id}: senão "reorder" seria lido como um id.
@app.put("/api/items/reorder", dependencies=[Depends(require_auth)])
async def reorder_items(request: Request):
    ids: list[str] = await request.json()
    with db() as con:
        for i, item_id in enumerate(ids):
            con.execute("UPDATE items SET ord=? WHERE id=?", (i, item_id))
        bump_version(con)
        con.commit()
    return {"ok": True}


@app.put("/api/items/{item_id}", dependencies=[Depends(require_auth)])
async def update_item(item_id: str, request: Request):
    body = await request.json()
    with db() as con:
        row = con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(404)
        con.execute("UPDATE items SET name=?,config=?,duration=?,active=? WHERE id=?", (
            body.get("name", row["name"]),
            json.dumps(body.get("config", json.loads(row["config"]))),
            max(3, int(body.get("duration", row["duration"]))),
            int(body.get("active", row["active"])),
            item_id))
        bump_version(con)
        con.commit()
    return {"ok": True}


@app.delete("/api/items/{item_id}", dependencies=[Depends(require_auth)])
def delete_item(item_id: str):
    with db() as con:
        con.execute("DELETE FROM items WHERE id=?", (item_id,))
        con.execute("DELETE FROM schedule WHERE kind='item' AND ref_id=?", (item_id,))
        bump_version(con)
        con.commit()
    return {"ok": True}


# ─── Grade horária (timeline) ─────────────────────────────────────────────────
#
# REGRA DE PRIORIDADE (a mesma explicada no painel):
#   1. Item avulso com bloco no horário atual → a TV mostra só esse item.
#      Ele "sobrepõe" temporariamente qualquer playlist da trilha base.
#   2. Senão, playlist com bloco no horário atual → a TV roda essa playlist.
#   3. Senão (ou se o bloco aponta para algo vazio/desativado) → Playlist padrão.
#   Dois blocos da MESMA trilha no mesmo horário: vence o que começou mais
#   tarde (o mais específico, ex.: 12:00–13:00 dentro de 08:00–18:00).
#   Se começarem juntos, vence o mais curto.

def _hhmm(minutes: int) -> str:
    return "24:00" if minutes == 1440 else f"{minutes // 60:02d}:{minutes % 60:02d}"


def _clean_block(b: dict, playlist_ids: set, item_ids: set) -> dict:
    kind, ref = b.get("kind"), str(b.get("ref_id", ""))
    if kind not in ("playlist", "item"):
        raise HTTPException(400, f"Tipo de bloco inválido: {kind}")
    if (kind == "playlist" and ref not in playlist_ids) or (kind == "item" and ref not in item_ids):
        raise HTTPException(400, "Bloco aponta para playlist/item que não existe mais")
    try:
        start = max(0, min(1439, int(b["start_min"])))
        end = max(start + 1, min(1440, int(b["end_min"])))
    except (KeyError, TypeError, ValueError):
        raise HTTPException(400, "Horário inválido no bloco")
    return {"id": str(b.get("id") or uuid.uuid4().hex[:12]), "kind": kind, "ref_id": ref,
            "start_min": start, "end_min": end}


@app.get("/api/schedule")
def get_schedule():
    with db() as con:
        rows = con.execute("SELECT id, kind, ref_id, start_min, end_min FROM schedule ORDER BY start_min").fetchall()
    return {"blocks": [dict(r) for r in rows]}


@app.put("/api/schedule", dependencies=[Depends(require_auth)])
async def save_schedule(request: Request):
    """Substitui a grade inteira (o painel sempre envia a lista completa)."""
    body = await request.json()
    with db() as con:
        pl = {r["id"] for r in con.execute("SELECT id FROM playlists")}
        it = {r["id"] for r in con.execute("SELECT id FROM items")}
        blocks = [_clean_block(b, pl, it) for b in body.get("blocks", [])]
        con.execute("DELETE FROM schedule")
        now = int(time.time())
        con.executemany("INSERT INTO schedule VALUES (?,?,?,?,?,?)",
                        [(b["id"], b["kind"], b["ref_id"], b["start_min"], b["end_min"], now) for b in blocks])
        bump_version(con)
        con.commit()
    return {"blocks": blocks}


def _pick_block(blocks: list[dict], kind: str, now_min: int) -> dict | None:
    hits = [b for b in blocks if b["kind"] == kind and b["start_min"] <= now_min < b["end_min"]]
    if not hits:
        return None
    return max(hits, key=lambda b: (b["start_min"], -(b["end_min"] - b["start_min"])))


def resolve_now(con: sqlite3.Connection, now: datetime | None = None) -> dict:
    """Decide o que a TV deve exibir agora, aplicando a regra de prioridade acima.

    `slot` identifica a decisão: quando muda (ex.: deu 12:00 e entrou outro bloco),
    o player interrompe o item atual e troca de conteúdo.
    """
    now = now or datetime.now()
    m = now.hour * 60 + now.minute
    blocks = [dict(r) for r in con.execute("SELECT * FROM schedule")]
    names = {r["id"]: r["name"] for r in con.execute("SELECT id, name FROM playlists")}

    def items_of(pid: str) -> list[dict]:
        rows = con.execute("SELECT * FROM items WHERE playlist_id=? AND active=1 ORDER BY ord, created_at", (pid,))
        return [item_dict(r) for r in rows]

    overlay = _pick_block(blocks, "item", m)
    if overlay:
        row = con.execute("SELECT * FROM items WHERE id=? AND active=1", (overlay["ref_id"],)).fetchone()
        if row:
            return {"slot": f"item:{overlay['id']}", "items": [item_dict(row)],
                    "source": {"kind": "item", "name": row["name"], "until": _hhmm(overlay["end_min"])}}

    base = _pick_block(blocks, "playlist", m)
    if base:
        its = items_of(base["ref_id"])
        if its:
            return {"slot": f"playlist:{base['id']}", "items": its,
                    "source": {"kind": "playlist", "name": names.get(base["ref_id"], "Playlist"),
                               "until": _hhmm(base["end_min"])}}

    upcoming = [b["start_min"] for b in blocks if b["start_min"] > m]
    return {"slot": "default", "items": items_of(DEFAULT_PLAYLIST),
            "source": {"kind": "default", "name": names.get(DEFAULT_PLAYLIST, "Playlist padrão"),
                       "until": _hhmm(min(upcoming)) if upcoming else None}}


@app.get("/api/player/state")
def player_state():
    with db() as con:
        state = resolve_now(con)
        ver = con.execute("SELECT val FROM version WHERE id=1").fetchone()
    state["version"] = ver["val"] if ver else 0
    state["server_time"] = datetime.now().strftime("%H:%M")
    return state


# ─── Upload e arquivos estáticos ──────────────────────────────────────────────

@app.post("/api/upload", dependencies=[Depends(require_auth)])
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE | ALLOWED_VIDEO:
        raise HTTPException(400, f"Tipo não permitido: {ext}")
    fname = f"{uuid.uuid4().hex[:12]}{ext}"
    async with aiofiles.open(UPLOADS_DIR / fname, "wb") as f:
        await f.write(await file.read())
    return {"filename": fname, "type": "image" if ext in ALLOWED_IMAGE else "video", "url": f"/uploads/{fname}"}


app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


# ─── Configurações ────────────────────────────────────────────────────────────

def load_settings() -> dict:
    with db() as con:
        rows = con.execute("SELECT key, value FROM settings").fetchall()
    base = {
        "weather_lat": WEATHER_LAT,
        "weather_lon": WEATHER_LON,
        "weather_city": WEATHER_CITY,
        "maps_api_key": MAPS_API_KEY,
        "ibge_code": IBGE_CODE,
    }
    base.update({r["key"]: r["value"] for r in rows})
    return base


@app.get("/api/settings")
def get_settings():
    return load_settings()


@app.put("/api/settings", dependencies=[Depends(require_auth)])
async def save_settings(request: Request):
    body = await request.json()
    with db() as con:
        for k, v in body.items():
            con.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (k, str(v)))
        con.commit()
    return {"ok": True}


# ─── Clima (Open-Meteo + alertas oficiais do INMET) ──────────────────────────

WX_TTL = 600
_wx_cache: dict = {"t": 0.0, "key": None, "data": None}
SEV_ORDER = {"red": 0, "orange": 1, "yellow": 2}


def _http_json(url: str, timeout: float = 8):
    req = urllib.request.Request(url, headers={"User-Agent": "AlavaVision/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _fetch_forecast(lat: str, lon: str) -> dict:
    q = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "forecast_days": 7,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,"
                   "wind_speed_10m,wind_gusts_10m,is_day,precipitation",
        "hourly": "precipitation_probability",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
                 "precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max,sunrise,sunset",
    })
    return _http_json(f"https://api.open-meteo.com/v1/forecast?{q}")


def _build_weather(raw: dict, city: str) -> dict:
    """Monta o JSON da tela de clima.

    Chuva — o que cada número significa (Open-Meteo):
      rain_prob       → probabilidade de chuva NA HORA ATUAL (série horária).
      rain_prob_rest  → maior probabilidade entre a hora atual e 23:59 de hoje.
                        É o número exibido como "máx. X% até o fim do dia".
      daily.rain_prob → `precipitation_probability_max`: a MAIOR probabilidade
                        horária do dia inteiro, incluindo horas que já passaram.
                        Era esse o "92% no dia" da versão 0.2.0 — por isso podia
                        mostrar 92% à tarde por causa de uma chuva da madrugada.
                        Continua sendo usado na faixa de 7 dias.
      daily.rain_sum  → volume previsto (mm) somado no dia.
    """
    cur, d, hr = raw["current"], raw["daily"], raw.get("hourly", {})
    hour_key = cur["time"][:13] + ":00"
    today = cur["time"][:10]
    times = hr.get("time", [])
    probs = hr.get("precipitation_probability", [])
    rain_now = probs[times.index(hour_key)] if hour_key in times else None
    rest = [p for t, p in zip(times, probs) if t[:10] == today and t >= hour_key and p is not None]
    daily = [{
        "date": d["time"][i],
        "code": d["weather_code"][i],
        "max": d["temperature_2m_max"][i],
        "min": d["temperature_2m_min"][i],
        "rain_prob": d["precipitation_probability_max"][i],
        "rain_sum": d["precipitation_sum"][i],
        "wind_max": d["wind_speed_10m_max"][i],
        "gust_max": d["wind_gusts_10m_max"][i],
    } for i in range(len(d["time"]))]
    return {
        "city": city,
        "current": {
            "temp": cur["temperature_2m"],
            "feels": cur["apparent_temperature"],
            "humidity": cur["relative_humidity_2m"],
            "code": cur["weather_code"],
            "wind": cur["wind_speed_10m"],
            "gust": cur["wind_gusts_10m"],
            "is_day": cur["is_day"],
            "precip": cur["precipitation"],
            "rain_prob": rain_now,
            "rain_prob_rest": max(rest) if rest else None,
        },
        "daily": daily,
        "sunrise": d["sunrise"][0],
        "sunset": d["sunset"][0],
    }


def _inmet_severity(text: str) -> str:
    t = text.lower()
    if "grande" in t:
        return "red"
    if "potencial" in t:
        return "yellow"
    if "perigo" in t:
        return "orange"
    return "yellow"


def _inmet_alerts(ibge: str) -> list[dict]:
    """Avisos ativos do INMET filtrados pelo código IBGE do município."""
    if not ibge:
        return []
    data = _http_json("https://apiprevmet3.inmet.gov.br/avisos/ativos", timeout=6)
    entries = []
    if isinstance(data, dict):
        for k in ("hoje", "futuro"):
            entries += data.get(k) or []
    elif isinstance(data, list):
        entries = data
    out, seen = [], set()
    for a in entries:
        if not isinstance(a, dict) or ibge not in str(a.get("geocodes", "")):
            continue
        title = a.get("descricao") or a.get("evento") or "Aviso meteorológico"
        sev_text = str(a.get("severidade", ""))
        sev = _inmet_severity(sev_text)
        if (title, sev) in seen:
            continue
        seen.add((title, sev))
        end = str(a.get("fim") or a.get("data_fim") or "")
        if a.get("hora_fim") and ":" not in end:
            end = f"{end} {a['hora_fim']}"
        out.append({"title": title, "severity": sev, "detail": sev_text, "end": end or None, "source": "INMET"})
    return out


@app.get("/api/weather")
def api_weather():
    s = load_settings()
    ibge = str(s.get("ibge_code") or "").strip()
    key = (s["weather_lat"], s["weather_lon"], ibge, s["weather_city"])
    now = time.time()
    if _wx_cache["data"] and _wx_cache["key"] == key and now - _wx_cache["t"] < WX_TTL:
        return _wx_cache["data"]
    try:
        w = _build_weather(_fetch_forecast(s["weather_lat"], s["weather_lon"]), s["weather_city"])
    except Exception as e:
        if _wx_cache["data"]:
            return _wx_cache["data"]
        raise HTTPException(502, f"Falha ao obter previsão: {e}")
    try:
        alerts = _inmet_alerts(ibge)
    except Exception:
        alerts = []
    w["alerts"] = sorted(alerts, key=lambda a: SEV_ORDER.get(a["severity"], 9))
    _wx_cache.update(t=now, key=key, data=w)
    return w


# ─── Telas exibidas pelo player (e pela pré-visualização do painel) ──────────

def view_html(body_content: str) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  html,body{{width:100%;height:100%;overflow:hidden;background:#000;color:#fff;font-family:system-ui,sans-serif}}
</style>
</head>
<body>{body_content}</body>
</html>""")


def _item_config(item_id: str) -> dict:
    with db() as con:
        row = con.execute("SELECT config FROM items WHERE id=?", (item_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    return json.loads(row["config"])


@app.get("/view/image/{item_id}")
def view_image(item_id: str):
    url = _item_config(item_id).get("url", "")
    return view_html(f"""
<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:#000">
  <img src="{url}" style="max-width:100%;max-height:100%;object-fit:contain">
</div>""")


@app.get("/view/video/{item_id}")
def view_video(item_id: str):
    url = _item_config(item_id).get("url", "")
    return view_html(f"""
<video src="{url}" autoplay muted loop playsinline
  style="width:100%;height:100%;object-fit:contain;background:#000"></video>""")


@app.get("/view/weather")
def view_weather():
    return FileResponse(str(STATIC_DIR / "weather.html"))


@app.get("/view/traffic")
def view_traffic():
    s = load_settings()
    lat, lon, maps_key = s["weather_lat"], s["weather_lon"], s["maps_api_key"]
    if maps_key:
        src = f"https://www.google.com/maps/embed/v1/view?key={maps_key}&center={lat},{lon}&zoom=13&maptype=roadmap"
    else:
        src = f"https://embed.waze.com/iframe?zoom=14&lat={lat}&lon={lon}&ct=livemap&pin=1"
    return view_html(f'<iframe style="width:100%;height:100%;border:0" src="{src}" allowfullscreen></iframe>')


@app.get("/view/message/{item_id}")
def view_message(item_id: str):
    cfg = _item_config(item_id)
    text = cfg.get("text", "")
    bg = cfg.get("bg_color", "#0a0a1a")
    fg = cfg.get("text_color", "#ffffff")
    size = cfg.get("font_size", 72)
    show_clock = "true" if cfg.get("show_clock", True) else "false"
    return view_html(f"""
<div style="width:100%;height:100%;display:flex;flex-direction:column;align-items:center;
  justify-content:center;background:{bg};gap:32px;padding:60px;text-align:center">
  <div id="clock" style="font-size:48px;opacity:.5;font-weight:200;letter-spacing:4px"></div>
  <div style="font-size:{size}px;font-weight:600;color:{fg};line-height:1.2;max-width:900px">{text}</div>
</div>
<script>
if({show_clock}){{
  function tick(){{
    const n=new Date();
    document.getElementById('clock').textContent=
      n.getHours().toString().padStart(2,'0')+':'+n.getMinutes().toString().padStart(2,'0');
  }}
  tick(); setInterval(tick,1000);
}}
</script>""")


# ─── Painel e arquivos do painel ──────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def admin():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.on_event("startup")
def startup():
    init_db()
    print(f"\n✅ Alava Vision {__version__} rodando em http://0.0.0.0:{PORT}/")
    print(f"   Login: {ADMIN_USER} / {ADMIN_PASSWORD}\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
