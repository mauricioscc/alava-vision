"""
Alava Vision — Servidor (server.py) · versão 0.9.0

COMO RODAR
    pip install -r requirements.txt
    python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload
    Painel ........ http://localhost:8080/   (usuário "admin", senha = ADMIN_PASSWORD do .env)
    Testes rápidos no navegador:
        http://localhost:8080/api/player/state  → o que o player deve exibir AGORA (resultado da grade)
        http://localhost:8080/api/schedule      → blocos salvos na timeline
        http://localhost:8080/api/weather       → dados de clima usados na tela de previsão
        http://localhost:8080/view/countdown/<id_do_item>  → contador regressivo de um item
        http://localhost:8080/view/html/<id_do_item>       → página HTML local de um item
    Aviso instantâneo (WebSocket) para o player:
        ws://localhost:8080/ws/player  → manda o estado ao conectar e de novo a cada mudança.
        No terminal do servidor aparecem "[push] player conectado/desconectado".

    Comparação de modelos de clima (0.8.1, temporária):
        data/wx_compare.csv  → uma linha por modelo a cada 9 min (abre no Excel).
        Desligar: WX_COMPARE=0 no .env e reiniciar o servidor.

COMO REVERTER
    Com Git (a partir da 0.3.0):  git log --oneline  e  git checkout <commit> -- server.py
    Para a 0.8.0 (antes da correção da garoa): copie backup_v0.8.0_20261118/server.py por cima do atual.
    Para a 0.8.1 (antes dos widgets de HTML e contador):  git checkout 3ac5a57 -- server.py player.py static/index.html
    Itens de HTML/contador criados na 0.9.0 ficam no banco; na 0.8.1 eles só aparecem sem tela.
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
    O que está no ar agora .......... resolve_now(), _pick_block(), current_state(), GET /api/player/state
    Aviso instantâneo (WebSocket) ... WS /ws/player, _players, _broadcast(), _push_watcher(),
                                      _notify_players() (middleware: avisa após salvar no painel)
    Upload e arquivos ............... POST /api/upload, /uploads/* e /assets/* (StaticFiles)
      HTML local (.html ou .zip) .... POST /api/upload-html, _extract_zip_safely(), _pick_html_entry(),
                                      pasta data/html/<id>/ servida em /html/*
    Configurações ................... load_settings(), GET/PUT /api/settings
    Clima ........................... _fetch_forecast(), _build_weather(), _inmet_alerts(), get_weather(),
                                      GET /api/weather
      atualização em 2º plano ....... _weather_refresher() (a cada 9 min, iniciada em startup())
      previsão embutida na tela ..... view_weather() troca WX_DATA_MARK pelo JSON do cache
      status do INMET ............... get_weather() define w["inmet_status"]: "ok" | "unavailable" | "disabled"
      filtro de garoa falsa ......... _fix_drizzle() (usada em _build_weather no "agora")
      comparação de modelos ......... _log_model_compare() → data/wx_compare.csv (WX_COMPARE no .env)
    Telas exibidas pelo player ...... /view/image/{id}, /view/video/{id}, /view/weather,
                                      /view/traffic, /view/message/{id},
                                      /view/html/{id} (redireciona para /html/...), /view/countdown/{id}
      vídeo repetir ou não .......... view_video(): config.loop (padrão True)
    Logo Alava ...................... faixa do topo em view_traffic(); na tela de clima, .brand em weather.html
                                      Só clima e trânsito exibem o logo; sites, imagens, vídeos e
                                      mensagens aparecem sem ele.
"""
import asyncio
import html
import json
import os
import secrets
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

__version__ = "0.9.0"

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
# Registro temporário de comparação entre modelos de clima (ligado por padrão; WX_COMPARE=0 desliga)
WX_COMPARE = os.getenv("WX_COMPARE", "1").strip() != "0"

ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
ALLOWED_VIDEO = {".mp4", ".webm", ".mov", ".avi"}

# Widget de HTML local (0.9.0): cada envio vira uma pasta em data/html/<id>/
HTML_DIR = DATA_DIR / "html"
HTML_DIR.mkdir(parents=True, exist_ok=True)
HTML_ZIP_MAX_FILES = 2000                 # limites contra .zip malformado ou "bomba"
HTML_ZIP_MAX_BYTES = 300 * 1024 * 1024    # 300 MB descompactado

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


def current_state() -> dict:
    """O que a TV deve exibir agora + número de versão (usado pela rota HTTP e pelo WebSocket)."""
    with db() as con:
        state = resolve_now(con)
        ver = con.execute("SELECT val FROM version WHERE id=1").fetchone()
    state["version"] = ver["val"] if ver else 0
    state["server_time"] = datetime.now().strftime("%H:%M")
    return state


@app.get("/api/player/state")
def player_state():
    return current_state()


# ─── Aviso instantâneo para os players (WebSocket) ────────────────────────────
#
# Antes, o player perguntava a cada 5 s "mudou alguma coisa?". Agora ele mantém uma
# conexão aberta em /ws/player e o servidor manda o estado novo assim que:
#   • alguém salva algo no painel (o middleware _notify_players acorda o vigia), ou
#   • a programação troca de bloco (o vigia confere a cada virada de minuto).
# "Mudou" = mudou a assinatura (version, slot), o mesmo critério que o player já usava.
# Se a conexão cair, o player volta a perguntar a cada 5 s pela rota HTTP até reconectar.

_players: dict[WebSocket, asyncio.Lock] = {}   # conexões abertas → trava de envio de cada uma
_state_changed: asyncio.Event | None = None    # criado no startup, dentro do loop do servidor
_push_task: asyncio.Task | None = None


def _signature(state: dict) -> tuple:
    return state.get("version"), state.get("slot")


async def _send(ws: WebSocket, text: str) -> None:
    # A trava evita dois envios ao mesmo tempo na mesma conexão (boas-vindas + aviso).
    async with _players[ws]:
        await ws.send_text(text)


async def _broadcast(state: dict) -> None:
    text = json.dumps(state, ensure_ascii=False)
    for ws in list(_players):
        try:
            await _send(ws, text)
        except Exception:
            _players.pop(ws, None)


async def _push_watcher() -> None:
    """Vigia: recalcula o estado quando o painel salva ou o minuto vira, e avisa se mudou."""
    last = None
    while True:
        _state_changed.clear()
        try:
            state = await asyncio.to_thread(current_state)
            sig = _signature(state)
            if last is not None and sig != last and _players:
                print(f"[push] programação mudou — avisando {len(_players)} player(s)")
                await _broadcast(state)
            last = sig
        except Exception as e:
            print(f"[push] falha ao conferir a programação: {e}")
        # A grade trabalha em minutos cheios: dorme até logo depois da próxima virada de minuto,
        # ou até o painel salvar alguma coisa (o que vier primeiro).
        now = datetime.now()
        wait = 60 - now.second - now.microsecond / 1e6 + 0.5
        try:
            await asyncio.wait_for(_state_changed.wait(), timeout=wait)
        except asyncio.TimeoutError:
            pass


@app.middleware("http")
async def _notify_players(request: Request, call_next):
    """Depois que uma alteração no painel termina (já gravada no banco), acorda o vigia."""
    response = await call_next(request)
    if (request.method in ("POST", "PUT", "DELETE") and request.url.path.startswith("/api/")
            and response.status_code < 400 and _state_changed is not None):
        _state_changed.set()
    return response


@app.websocket("/ws/player")
async def ws_player(ws: WebSocket):
    await ws.accept()
    _players[ws] = asyncio.Lock()
    who = ws.client.host if ws.client else "?"
    print(f"[push] player conectado ({who}) — {len(_players)} conectado(s)")
    try:
        await _send(ws, json.dumps(await asyncio.to_thread(current_state), ensure_ascii=False))
        while True:
            await ws.receive_text()  # o player não envia nada; isso só percebe a desconexão
    except WebSocketDisconnect:
        pass
    finally:
        _players.pop(ws, None)
        print(f"[push] player desconectado ({who}) — {len(_players)} conectado(s)")


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


def _pick_html_entry(folder: Path) -> Path | None:
    """Página inicial de um .zip: index.html na raiz, ou dentro de uma única pasta, ou o 1º .html."""
    for cand in (folder / "index.html", folder / "index.htm"):
        if cand.is_file():
            return cand
    subdirs = [p for p in folder.iterdir() if p.is_dir()]
    files = [p for p in folder.iterdir() if p.is_file()]
    if len(subdirs) == 1 and not files:          # zip com tudo dentro de uma pasta, ex.: painel/index.html
        return _pick_html_entry(subdirs[0])
    pages = sorted(folder.rglob("*.htm*"), key=lambda p: (len(p.parts), str(p).lower()))
    return pages[0] if pages else None


def _extract_zip_safely(data: bytes, dest: Path) -> None:
    """Descompacta sem deixar nenhum arquivo sair de `dest` (nomes como ../../server.py)."""
    import io
    import zipfile
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise HTTPException(400, "Arquivo .zip inválido")
    infos = [i for i in zf.infolist() if not i.is_dir()]
    if len(infos) > HTML_ZIP_MAX_FILES:
        raise HTTPException(400, f"O .zip tem arquivos demais (máximo {HTML_ZIP_MAX_FILES})")
    if sum(i.file_size for i in infos) > HTML_ZIP_MAX_BYTES:
        raise HTTPException(400, "O .zip descompactado passa de 300 MB")
    root = dest.resolve()
    for info in infos:
        target = (dest / info.filename).resolve()
        if root not in target.parents:
            raise HTTPException(400, f"Caminho inválido dentro do .zip: {info.filename}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, open(target, "wb") as out:
            out.write(src.read())


@app.post("/api/upload-html", dependencies=[Depends(require_auth)])
async def upload_html(file: UploadFile = File(...)):
    """Widget de HTML local: recebe um .html (página única) ou um .zip (página + CSS/imagens/scripts).

    Cada envio ganha uma pasta própria em data/html/<id>/, servida em /html/<id>/...
    Links relativos da página (style.css, img/logo.png) funcionam porque a pasta inteira é servida.
    """
    import shutil
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".html", ".htm", ".zip"):
        raise HTTPException(400, "Envie um arquivo .html ou .zip")
    data = await file.read()
    folder_id = uuid.uuid4().hex[:12]
    dest = HTML_DIR / folder_id
    dest.mkdir(parents=True)
    try:
        if ext == ".zip":
            _extract_zip_safely(data, dest)
            entry = _pick_html_entry(dest)
            if not entry:
                raise HTTPException(400, "Nenhuma página .html encontrada dentro do .zip")
        else:
            entry = dest / "index.html"
            entry.write_bytes(data)
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    rel = entry.relative_to(HTML_DIR).as_posix()
    return {"url": "/html/" + urllib.parse.quote(rel), "file": file.filename, "entry": rel.split("/", 1)[1]}


app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/html", StaticFiles(directory=str(HTML_DIR)), name="html")
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


# Garoa "fantasma": o modelo padrão da Open-Meteo às vezes devolve garoa (51/53) com
# 0,1 mm num dia de sol, e a TV mostrava chuva. Abaixo deste volume, garoa vira
# "parcialmente nublado" (código 2). Chuva de verdade (61+, pancadas, trovoadas) não muda.
DRIZZLE_CODES = (51, 53)
DRIZZLE_MIN_MM = 0.2


def _fix_drizzle(code, precip):
    """Troca garoa fraca/moderada com menos de DRIZZLE_MIN_MM por parcialmente nublado."""
    if code in DRIZZLE_CODES and (precip or 0) < DRIZZLE_MIN_MM:
        return 2
    return code


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
            "code": _fix_drizzle(cur["weather_code"], cur["precipitation"]),
            "code_raw": cur["weather_code"],   # código original do modelo, para conferência
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


def get_weather(force: bool = False) -> dict:
    """Previsão + alertas, com cache de 10 min. Em falha de rede devolve a última previsão boa.

    `force=True` ignora o cache (usado pela atualização em segundo plano).
    """
    s = load_settings()
    ibge = str(s.get("ibge_code") or "").strip()
    key = (s["weather_lat"], s["weather_lon"], ibge, s["weather_city"])
    now = time.time()
    if not force and _wx_cache["data"] and _wx_cache["key"] == key and now - _wx_cache["t"] < WX_TTL:
        return _wx_cache["data"]
    try:
        w = _build_weather(_fetch_forecast(s["weather_lat"], s["weather_lon"]), s["weather_city"])
    except Exception as e:
        if _wx_cache["data"]:
            return _wx_cache["data"]
        raise HTTPException(502, f"Falha ao obter previsão: {e}")
    try:
        alerts = _inmet_alerts(ibge)
        inmet_status = "ok"
    except Exception:
        alerts = []
        inmet_status = "unavailable"
    w["alerts"] = sorted(alerts, key=lambda a: SEV_ORDER.get(a["severity"], 9))
    w["inmet_status"] = inmet_status if ibge else "disabled"
    w["updated_at"] = datetime.now().strftime("%H:%M")
    _wx_cache.update(t=now, key=key, data=w)
    return w


@app.get("/api/weather")
def api_weather():
    return get_weather()


# Mantém o cache sempre "quente": a cada 9 min (antes de vencer o TTL de 10) busca a
# previsão em segundo plano. Assim a tela de clima nunca espera a internet ao abrir.
WX_REFRESH_EVERY = 540

# ─── Comparação de modelos (temporária, iniciada em 18/11/2026, revisar em 02/12/2026) ──
# A cada atualização grava em data/wx_compare.csv o "agora" de cada modelo, para decidir
# com dados se vale trocar o modelo padrão pelo ECMWF. Separador ";" para abrir direto
# no Excel em português. Falhas aqui nunca afetam a tela de clima.
WX_COMPARE_FILE = DATA_DIR / "wx_compare.csv"
WX_COMPARE_MODELS = ("best_match", "ecmwf_ifs025")   # best_match = o que a TV usa hoje
WX_COMPARE_HEADER = ("data_hora;modelo;temp_c;codigo_modelo;codigo_exibido;"
                     "descricao_exibida;chuva_mm;nuvens_pct;umidade_pct\n")
WX_CODE_PT = {0: "Céu limpo", 1: "Predomínio de sol", 2: "Parcialmente nublado", 3: "Nublado",
              45: "Neblina", 48: "Neblina", 51: "Garoa fraca", 53: "Garoa", 55: "Garoa intensa",
              61: "Chuva fraca", 63: "Chuva", 65: "Chuva forte", 80: "Pancadas de chuva",
              81: "Pancadas fortes", 82: "Pancadas violentas", 95: "Trovoadas",
              96: "Trovoadas com granizo", 99: "Trovoadas com granizo"}


def _log_model_compare():
    s = load_settings()
    lines = []
    for model in WX_COMPARE_MODELS:
        q = urllib.parse.urlencode({
            "latitude": s["weather_lat"], "longitude": s["weather_lon"], "timezone": "auto",
            "models": model,
            "current": "temperature_2m,weather_code,precipitation,cloud_cover,relative_humidity_2m",
        })
        c = _http_json(f"https://api.open-meteo.com/v1/forecast?{q}")["current"]
        shown = _fix_drizzle(c["weather_code"], c["precipitation"])
        lines.append(";".join(str(v).replace(".", ",") if isinstance(v, float) else str(v) for v in (
            c["time"].replace("T", " "), model, c["temperature_2m"], c["weather_code"], shown,
            WX_CODE_PT.get(shown, shown), c["precipitation"], c["cloud_cover"],
            c["relative_humidity_2m"])) + "\n")
    new = not WX_COMPARE_FILE.exists()
    with open(WX_COMPARE_FILE, "a", encoding="utf-8-sig" if new else "utf-8") as f:
        if new:
            f.write(WX_COMPARE_HEADER)
        f.writelines(lines)


def _weather_refresher():
    while True:
        try:
            get_weather(force=True)
        except Exception as e:
            print(f"[clima] falha ao atualizar a previsão em segundo plano: {e}")
        if WX_COMPARE:
            try:
                _log_model_compare()
            except Exception as e:
                print(f"[clima] falha ao gravar a comparação de modelos: {e}")
        time.sleep(WX_REFRESH_EVERY)


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
    """Vídeo em tela cheia. config.loop (padrão True, como antes da 0.9.0):
    True  → repete até acabar a duração do item;
    False → toca uma vez; o player percebe o fim (video.ended) e passa para o próximo item.
    """
    cfg = _item_config(item_id)
    url = html.escape(cfg.get("url", ""))
    loop = " loop" if cfg.get("loop", True) else ""
    return view_html(f"""
<video src="{url}" autoplay muted{loop} playsinline
  style="width:100%;height:100%;object-fit:contain;background:#000"></video>""")


@app.get("/view/html/{item_id}")
def view_local_html(item_id: str):
    """Widget de HTML local: redireciona para a página enviada (data/html/<id>/...)."""
    from fastapi.responses import RedirectResponse
    url = _item_config(item_id).get("url", "")
    if not url.startswith("/html/"):
        raise HTTPException(404, "Página HTML não encontrada")
    return RedirectResponse(url)


@app.get("/view/countdown/{item_id}")
def view_countdown(item_id: str):
    """Contador regressivo até config.target ("AAAA-MM-DDTHH:MM", horário do computador da TV).

    Mostra dias / horas / minutos / segundos. Quando chega a hora, exibe config.end_text.
    Com config.hide_after, o player deixa de exibir o item depois do fim (countdown_visible()).
    """
    cfg = _item_config(item_id)
    title = html.escape(cfg.get("title", ""))
    end_text = html.escape(cfg.get("end_text", "") or "Chegou a hora!")
    bg = html.escape(cfg.get("bg_color", "#0a0a1a"))
    fg = html.escape(cfg.get("text_color", "#ffffff"))
    target = json.dumps(cfg.get("target", ""))
    show_sec = "true" if cfg.get("show_seconds", True) else "false"
    return view_html(f"""
<style>
  .cd{{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
    gap:5vh;background:{bg};color:{fg};text-align:center;padding:4vh 4vw;font-variant-numeric:tabular-nums}}
  .cd-title{{font-size:6.5vh;font-weight:600;line-height:1.15;max-width:90vw}}
  .cd-tiles{{display:flex;gap:2.4vw}}
  .cd-tile{{min-width:15vw;padding:3vh 1.6vw;border-radius:2.4vh;background:color-mix(in srgb,{fg} 9%,transparent)}}
  .cd-num{{font-size:16vh;font-weight:700;line-height:1}}
  .cd-lab{{margin-top:1.6vh;font-size:2.6vh;letter-spacing:.25em;text-transform:uppercase;opacity:.7}}
  .cd-when{{font-size:3vh;opacity:.65}}
  .cd-end{{font-size:11vh;font-weight:700;line-height:1.15;max-width:90vw}}
</style>
<div class="cd">
  <div class="cd-title">{title}</div>
  <div class="cd-tiles" id="tiles"></div>
  <div class="cd-end" id="end" hidden>{end_text}</div>
  <div class="cd-when" id="when"></div>
</div>
<script>
const TARGET = {target}, SHOW_SEC = {show_sec};
const t = TARGET ? new Date(TARGET) : null;   // "AAAA-MM-DDTHH:MM" sem fuso = horário local
const pad = n => String(n).padStart(2, '0');
if (t && !isNaN(t)) {{
  const dias = ['domingo','segunda','terça','quarta','quinta','sexta','sábado'];
  document.getElementById('when').textContent =
    `até ${{dias[t.getDay()]}}, ${{pad(t.getDate())}}/${{pad(t.getMonth()+1)}}/${{t.getFullYear()}} às ${{pad(t.getHours())}}:${{pad(t.getMinutes())}}`;
}}
function tile(n, lab) {{ return `<div class="cd-tile"><div class="cd-num">${{n}}</div><div class="cd-lab">${{lab}}</div></div>`; }}
function tick() {{
  if (!t || isNaN(t)) {{ document.getElementById('tiles').innerHTML = ''; return; }}
  let s = Math.floor((t - Date.now()) / 1000);
  if (s <= 0) {{
    document.getElementById('tiles').hidden = true;
    document.getElementById('when').hidden = true;
    document.getElementById('end').hidden = false;
    return;
  }}
  const d = Math.floor(s / 86400); s %= 86400;
  const h = Math.floor(s / 3600); s %= 3600;
  const m = Math.floor(s / 60); s %= 60;
  // Dias só aparecem se faltar 1 dia ou mais; segundos, se a opção estiver ligada.
  document.getElementById('tiles').innerHTML =
    (d ? tile(d, d === 1 ? 'dia' : 'dias') : '') + tile(pad(h), 'horas') + tile(pad(m), 'min') +
    (SHOW_SEC ? tile(pad(s), 'seg') : '');
}}
tick(); setInterval(tick, 1000);
</script>""")


WX_DATA_MARK = "/*__WX_DATA__*/null"


@app.get("/view/weather")
def view_weather():
    """Tela de clima já com a previsão embutida, para abrir pronta (sem "Carregando…").

    O HTML tem `let W = /*__WX_DATA__*/null;` e a marca é trocada pelo JSON do cache.
    Se ainda não houver previsão, a página recebe null e busca /api/weather sozinha.
    `<\\/` evita que um texto com "</script>" nos dados feche a tag antes da hora.
    """
    page = (STATIC_DIR / "weather.html").read_text(encoding="utf-8")
    try:
        data = json.dumps(get_weather(), ensure_ascii=False).replace("</", "<\\/")
    except HTTPException:
        data = "null"
    return HTMLResponse(page.replace(WX_DATA_MARK, data, 1), headers={"Cache-Control": "no-store"})


@app.get("/view/traffic")
def view_traffic():
    """Mapa de trânsito com uma faixa no topo: logo Alava à esquerda, título e relógio à direita.

    O logo fica na faixa (e não por cima do mapa) porque o canto superior esquerdo do Waze
    e do Google Maps já tem a busca/cartão do próprio mapa. A faixa mantém o logo no mesmo
    lugar e tamanho da tela de clima (canto superior esquerdo, 4,2% da altura).
    """
    s = load_settings()
    lat, lon, maps_key = s["weather_lat"], s["weather_lon"], s["maps_api_key"]
    city = html.escape(s["weather_city"] or "")
    if maps_key:
        src = f"https://www.google.com/maps/embed/v1/view?key={maps_key}&center={lat},{lon}&zoom=13&maptype=roadmap"
    else:
        src = f"https://embed.waze.com/iframe?zoom=14&lat={lat}&lon={lon}&ct=livemap&pin=1"
    return view_html(f"""
<div style="position:fixed;inset:0;display:flex;flex-direction:column;background:#0b1220">
  <header style="height:9vh;flex:none;display:flex;align-items:center;justify-content:space-between;
    padding:0 1.8vw;color:#fff;font-variant-numeric:tabular-nums">
    <img src="/assets/watermark.png" alt="Alava" style="height:clamp(26px,4.2vh,72px);width:auto;opacity:.9">
    <div style="display:flex;align-items:baseline;gap:2vw">
      <span style="font-size:2.2vh;font-weight:600;letter-spacing:.2em;text-transform:uppercase;opacity:.85">
        Trânsito agora{' · ' + city if city else ''}</span>
      <span id="clock" style="font-size:3.6vh;font-weight:300"></span>
    </div>
  </header>
  <iframe style="flex:1;width:100%;border:0" src="{src}" allowfullscreen></iframe>
</div>
<script>
function tick(){{const n=new Date();document.getElementById('clock').textContent=
  String(n.getHours()).padStart(2,'0')+':'+String(n.getMinutes()).padStart(2,'0');}}
tick(); setInterval(tick, 1000);
</script>""")


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
    threading.Thread(target=_weather_refresher, name="clima", daemon=True).start()
    print(f"\n✅ Alava Vision {__version__} rodando em http://0.0.0.0:{PORT}/")
    print(f"   Login: {ADMIN_USER} / {ADMIN_PASSWORD}\n")


@app.on_event("startup")
async def start_push_watcher():
    global _state_changed, _push_task
    _state_changed = asyncio.Event()
    # Guardar a referência: uma tarefa sem referência pode ser recolhida pelo Python.
    _push_task = asyncio.create_task(_push_watcher(), name="push")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
