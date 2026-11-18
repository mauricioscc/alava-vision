"""
Alava Vision — Servidor (server.py) · versão 0.12.0

COMO RODAR
    pip install -r requirements.txt
    python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload
    Painel ........ http://localhost:8080/   (usuário "admin", senha = ADMIN_PASSWORD do .env)
    Testes rápidos no navegador:
        http://localhost:8080/api/player/state  → o que o player deve exibir AGORA (resultado da grade)
        http://localhost:8080/api/schedule      → blocos da régua "Todos os dias"
        http://localhost:8080/api/schedule?scope=wd:1            → régua de segunda-feira (wd:1..wd:7)
        http://localhost:8080/api/schedule?scope=date:2026-12-24 → exceção de uma data
        http://localhost:8080/api/schedule/rulers               → réguas próprias criadas
        http://localhost:8080/api/calendar?month=2026-12        → panorama do mês (régua de cada dia)
        http://localhost:8080/api/weather       → dados de clima usados na tela de previsão
        http://localhost:8080/view/countdown/<id_do_item>  → contador regressivo de um item
        http://localhost:8080/view/html/<id_do_item>       → página HTML local de um item
        http://localhost:8080/view/message-preview?c={"text":"Oi","bg_mode":"gradient"}  → prévia de mensagem
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
    Para a 0.11.0 (antes do botão de tema claro/escuro, que só muda o painel):
        git checkout 6efc5ba -- static/index.html
    Para a 0.10.0 (antes do calendário e das réguas por dia da semana):
        git checkout 8c60d7f -- server.py static/index.html
        A 0.10.0 lê só a régua "Todos os dias" (os blocos das outras réguas ficam no banco, ignorados).
        Para limpar: DELETE FROM schedule WHERE scope<>'all'; DELETE FROM rulers;
    Para a 0.9.0 (antes da mensagem avançada, RSS, curiosidades e voz):
        git checkout 027e198 -- server.py player.py static/index.html
        Mensagens novas continuam abrindo na 0.9.0, só sem as opções extras (fundo, fonte...).
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
    Playlists ....................... GET/POST /api/playlists, PUT/DELETE /api/playlists/{id},
                                      POST /api/playlists/{id}/duplicate (cópia com todos os itens)
    Itens ........................... GET /api/playlist, POST /api/items,
                                      PUT /api/items/reorder, PUT/DELETE /api/items/{id},
                                      POST /api/items/{id}/duplicate (cópia logo abaixo), _copy_item()
    Grade horária (timeline) ........ GET/PUT/DELETE /api/schedule (?scope=), _clean_block(), _write_ruler()
      réguas por dia / exceções ..... tabela rulers + coluna schedule.scope; _check_scope(), scope_label(),
                                      ruler_for_day() (PRIORIDADE: exceção > dia da semana > Todos os dias)
      dias úteis / copiar ........... POST /api/schedule/copy, GET /api/schedule/rulers
      calendário (panorama do mês) .. GET /api/calendar?month=AAAA-MM (régua, blocos, feriado, datas da lista
                                      e avisos de cada dia)
    Avisos por data ................. playlist reservada NOTICE_PLAYLIST ('avisos'), config.notice; notice_date()
                                      (repete todo ano seguindo feriado/data móvel), notice_occurrence(),
                                      notices_now() → intercalados no fim da playlist em resolve_now();
                                      GET /api/notices; contador anual em view_countdown()
    Na TV agora / pular item ........ POST /api/player/now (o player informa, só localhost), GET /api/player/now,
                                      POST /api/player/skip (_skip_seq → state["skip"] → WebSocket)
    O que está no ar agora .......... resolve_now() (escolhe a régua do dia), _pick_block(), current_state(),
                                      GET /api/player/state (campo "ruler" = régua em uso hoje)
    Aviso instantâneo (WebSocket) ... WS /ws/player, _players, _broadcast(), _push_watcher(),
                                      _notify_players() (middleware: avisa após salvar no painel)
    Upload e arquivos ............... POST /api/upload, /uploads/* e /assets/* (StaticFiles)
      HTML local (.html ou .zip) .... POST /api/upload-html, _extract_zip_safely(), _pick_html_entry(),
                                      pasta data/html/<id>/ servida em /html/*
      buscar imagens na web ......... GET /api/image-search (_search_pexels / _search_openverse, PEXELS_API_KEY),
                                      POST /api/image-import (só URLs de busca recente: _img_allowed)
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
      notícias (RSS) ................ /view/news/{id} (logo Alava no cabeçalho: config.show_logo, .top .logo), GET /api/news/{id}, POST /api/news-test,
                                      get_news() (filtro, sem repetidas), _fetch_feed() (cache NEWS_TTL),
                                      _parse_feed() (RSS e Atom), _warm_news() (em 2º plano, com o clima)
      curiosidades e datas .......... /view/today (?d=AAAA-MM-DD), GET /api/today, GET/PUT /api/curiosities,
                                      POST /api/curiosities/reset, today_info(), parse_curio(), holidays()
                                      (BrasilAPI → data/feriados_AAAA.json), today_auto_settings();
                                      lista: conteudo/datas_comemorativas.txt → data/datas_comemorativas.txt
                                      current_state()['today'] = {count, auto} para o player
      voz (Piper, offline) .......... GET /api/tts/{id}.wav, POST /api/tts-preview, GET /api/tts-status,
                                      POST /api/tts-install (roda ferramentas/instalar_voz.py), tts_wav()
                                      (cache data/tts/, TTS_RATES), _speech_text(); Piper em ferramentas/piper/
      mensagem ...................... view_message() e view_message_preview() → _render_message()
                                      (fundo sólido/degradê/imagem, MSG_FONTS, MSG_ANIMS, _css_color())
    Logo Alava ...................... faixa do topo em view_traffic(); na tela de clima, .brand em weather.html;
                                      nas notícias, cabeçalho de view_news() (0.11.0, pode desligar no item).
                                      Sites, imagens, vídeos e mensagens aparecem sem ele.
"""
import asyncio
import html
import json
import os
import re as _re
import secrets
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
import uuid
from datetime import date as _date, datetime, timedelta as _timedelta
from pathlib import Path

import aiofiles
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

__version__ = "0.12.0"

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
# Busca de imagens na web (0.10.0): com chave usa o Pexels; sem chave, o Openverse (sem cadastro)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
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
        # 0.11.0: playlist reservada dos avisos por data (fica fora das listas do painel)
        con.execute("INSERT OR IGNORE INTO playlists VALUES (?,?,?)",
                    ("avisos", "Avisos por data", int(time.time())))
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
        # 0.11.0: cada bloco pertence a uma "régua" (scope). Blocos antigos ficam em 'all'
        # ("Todos os dias"), então quem atualiza continua com a mesma programação.
        scols = {r["name"] for r in con.execute("PRAGMA table_info(schedule)")}
        if "scope" not in scols:
            con.execute("ALTER TABLE schedule ADD COLUMN scope TEXT NOT NULL DEFAULT 'all'")
        con.execute("CREATE INDEX IF NOT EXISTS schedule_scope ON schedule(scope)")
        # Réguas próprias criadas (dia da semana 'wd:1'..'wd:7' ou exceção 'date:AAAA-MM-DD').
        # A linha existir já basta: uma régua própria VAZIA também vale (o dia inteiro na
        # Playlist padrão), por isso não dá para deduzir isso só pelos blocos.
        con.execute("""
            CREATE TABLE IF NOT EXISTS rulers (
                scope      TEXT PRIMARY KEY,
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
            WHERE p.id != ?
            GROUP BY p.id ORDER BY (p.id != ?), p.created_at""", (NOTICE_PLAYLIST, DEFAULT_PLAYLIST)).fetchall()
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


@app.post("/api/playlists/{pid}/duplicate", dependencies=[Depends(require_auth)])
async def duplicate_playlist(pid: str, request: Request):
    """Cria uma playlist nova com cópias de todos os itens (mesma ordem, mesmo ativo/desativado).
    A programação (blocos da timeline) não é copiada. Corpo: {"name": "Nome da cópia"}."""
    if pid == NOTICE_PLAYLIST:
        raise HTTPException(400, "A playlist dos avisos por data não pode ser duplicada")
    name = str((await request.json()).get("name", "")).strip()
    with db() as con:
        src = con.execute("SELECT name FROM playlists WHERE id=?", (pid,)).fetchone()
        if not src:
            raise HTTPException(404)
        new_id = uuid.uuid4().hex[:12]
        name = name or f"{src['name']} (cópia)"
        con.execute("INSERT INTO playlists VALUES (?,?,?)", (new_id, name, int(time.time())))
        rows = con.execute("SELECT * FROM items WHERE playlist_id=? ORDER BY ord, created_at", (pid,)).fetchall()
        for i, r in enumerate(rows):
            _copy_item(con, r, new_id, i, r["name"])
        bump_version(con)
        con.commit()
    return {"id": new_id, "name": name, "items": len(rows)}


@app.delete("/api/playlists/{pid}", dependencies=[Depends(require_auth)])
def delete_playlist(pid: str):
    if pid == DEFAULT_PLAYLIST:
        raise HTTPException(400, "A playlist padrão não pode ser excluída")
    if pid == NOTICE_PLAYLIST:
        raise HTTPException(400, "A playlist dos avisos por data é do sistema")
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


# ─── Duplicar (0.11.0) ────────────────────────────────────────────────────────
# A cópia aponta para os mesmos arquivos (imagem, vídeo, HTML em data/uploads e data/html):
# remover um item não apaga arquivos, então original e cópia continuam funcionando sozinhos.

def _copy_item(con: sqlite3.Connection, row: sqlite3.Row, playlist_id: str, ord_: int, name: str) -> str:
    new_id = uuid.uuid4().hex[:12]
    con.execute("INSERT INTO items (id,type,name,config,duration,active,ord,created_at,playlist_id) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (new_id, row["type"], name, row["config"], row["duration"], row["active"], ord_,
                 int(time.time()), playlist_id))
    return new_id


@app.post("/api/items/{item_id}/duplicate", dependencies=[Depends(require_auth)])
def duplicate_item(item_id: str):
    """Copia o item para logo abaixo dele na mesma playlist, com o nome "… (cópia)"."""
    with db() as con:
        row = con.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(404)
        # Reorganiza a ordem da playlist (0, 1, 2...) e abre espaço logo depois do original
        ids = [r["id"] for r in con.execute("SELECT id FROM items WHERE playlist_id=? ORDER BY ord, created_at",
                                            (row["playlist_id"],))]
        pos = ids.index(item_id)
        for i, iid in enumerate(ids):
            con.execute("UPDATE items SET ord=? WHERE id=?", (i if i <= pos else i + 1, iid))
        new_id = _copy_item(con, row, row["playlist_id"], pos + 1, f"{row['name']} (cópia)")
        bump_version(con)
        con.commit()
    return {"id": new_id}


@app.delete("/api/items/{item_id}", dependencies=[Depends(require_auth)])
def delete_item(item_id: str):
    with db() as con:
        con.execute("DELETE FROM items WHERE id=?", (item_id,))
        con.execute("DELETE FROM schedule WHERE kind='item' AND ref_id=?", (item_id,))
        bump_version(con)
        con.commit()
    return {"ok": True}


# ─── Grade horária (timeline) e calendário ────────────────────────────────────
#
# RÉGUAS (0.11.0). Uma "régua" é a grade de 00:00 a 23:59 de um dia. Existem três níveis:
#   'all'               → "Todos os dias" (a régua única das versões anteriores);
#   'wd:1' … 'wd:7'     → régua própria de um dia da semana (1 = segunda … 7 = domingo,
#                         como date.isoweekday()). "Dias úteis" = copiar para wd:1..wd:5;
#   'date:AAAA-MM-DD'   → exceção de uma data específica (feriado, evento...).
#
# QUAL RÉGUA VALE NUM DIA (ruler_for_day). A régua é escolhida INTEIRA, não bloco a bloco:
#   1. existe exceção para a data              → usa a exceção;
#   2. senão, o dia da semana tem régua própria → usa a do dia da semana;
#   3. senão                                    → usa "Todos os dias".
#   Uma régua própria vazia também conta: o dia fica todo na Playlist padrão.
#   Para "só mudar o almoço de sexta", o painel cria a régua de sexta copiando a de
#   "Todos os dias" e aí se edita só o trecho desejado.
#
# DENTRO DA RÉGUA ESCOLHIDA (resolve_now), a mesma regra de sempre:
#   1. Item avulso com bloco no horário atual → a TV mostra só esse item.
#      Ele "sobrepõe" temporariamente qualquer playlist da trilha base.
#   2. Senão, playlist com bloco no horário atual → a TV roda essa playlist.
#   3. Senão (ou se o bloco aponta para algo vazio/desativado) → Playlist padrão (fallback).
#   Dois blocos da MESMA trilha no mesmo horário: vence o que começou mais
#   tarde (o mais específico, ex.: 12:00–13:00 dentro de 08:00–18:00).
#   Se começarem juntos, vence o mais curto.

WEEKDAY_NAMES = {1: "Segunda-feira", 2: "Terça-feira", 3: "Quarta-feira", 4: "Quinta-feira",
                 5: "Sexta-feira", 6: "Sábado", 7: "Domingo"}
_SCOPE_RE = _re.compile(r"^(all|wd:[1-7]|date:\d{4}-\d{2}-\d{2})$")


def _hhmm(minutes: int) -> str:
    return "24:00" if minutes == 1440 else f"{minutes // 60:02d}:{minutes % 60:02d}"


def _check_scope(scope: str | None) -> str:
    """Valida o nome da régua (padrão 'all', compatível com o painel antigo)."""
    scope = (scope or "all").strip()
    if not _SCOPE_RE.match(scope):
        raise HTTPException(400, f"Régua inválida: {scope}")
    if scope.startswith("date:"):
        try:
            _date.fromisoformat(scope[5:])
        except ValueError:
            raise HTTPException(400, f"Data inválida: {scope[5:]}")
    return scope


def scope_label(scope: str) -> str:
    if scope == "all":
        return "Todos os dias"
    if scope.startswith("wd:"):
        return WEEKDAY_NAMES[int(scope[3:])]
    d = _date.fromisoformat(scope[5:])
    return f"Exceção {d.strftime('%d/%m/%Y')}"


def _custom_scopes(con: sqlite3.Connection) -> set[str]:
    return {r["scope"] for r in con.execute("SELECT scope FROM rulers")}


def ruler_for_day(day: _date, custom: set[str]) -> str:
    """Aplica a hierarquia: exceção da data > régua do dia da semana > Todos os dias."""
    exc = f"date:{day.isoformat()}"
    if exc in custom:
        return exc
    wd = f"wd:{day.isoweekday()}"
    if wd in custom:
        return wd
    return "all"


def _blocks_of(con: sqlite3.Connection, scope: str) -> list[dict]:
    rows = con.execute("SELECT id, kind, ref_id, start_min, end_min FROM schedule WHERE scope=? "
                       "ORDER BY start_min", (scope,)).fetchall()
    return [dict(r) for r in rows]


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


def _write_ruler(con: sqlite3.Connection, scope: str, blocks: list[dict]) -> list[dict]:
    """Troca os blocos de uma régua. Os ids são únicos no banco inteiro: um id que já existe
    em OUTRA régua (ex.: blocos copiados no painel) ganha um id novo."""
    pl = {r["id"] for r in con.execute("SELECT id FROM playlists")}
    it = {r["id"] for r in con.execute("SELECT id FROM items")}
    taken = {r["id"] for r in con.execute("SELECT id FROM schedule WHERE scope<>?", (scope,))}
    clean, seen = [], set()
    for b in blocks:
        c = _clean_block(b, pl, it)
        if c["id"] in taken or c["id"] in seen:
            c["id"] = uuid.uuid4().hex[:12]
        seen.add(c["id"])
        clean.append(c)
    now = int(time.time())
    con.execute("DELETE FROM schedule WHERE scope=?", (scope,))
    con.executemany("INSERT INTO schedule (id, kind, ref_id, start_min, end_min, created_at, scope) "
                    "VALUES (?,?,?,?,?,?,?)",
                    [(b["id"], b["kind"], b["ref_id"], b["start_min"], b["end_min"], now, scope) for b in clean])
    if scope != "all":
        con.execute("INSERT OR IGNORE INTO rulers VALUES (?,?)", (scope, now))
    return clean


@app.get("/api/schedule")
def get_schedule(scope: str = "all"):
    """Blocos de uma régua. `custom` diz se ela existe; se não existir, `inherits` diz qual
    régua vale no lugar dela (e `blocks` traz os blocos dessa, só para mostrar)."""
    scope = _check_scope(scope)
    with db() as con:
        custom = _custom_scopes(con)
        own = scope == "all" or scope in custom
        if own:
            inherits = None
        elif scope.startswith("date:"):
            inherits = ruler_for_day(_date.fromisoformat(scope[5:]), custom)
        else:
            inherits = "all"
        blocks = _blocks_of(con, scope if own else inherits)
    return {"scope": scope, "label": scope_label(scope), "custom": own, "inherits": inherits,
            "inherits_label": scope_label(inherits) if inherits else None, "blocks": blocks}


@app.get("/api/schedule/rulers")
def list_rulers():
    """Réguas próprias criadas, com a quantidade de blocos de cada uma."""
    with db() as con:
        counts = {r["scope"]: r["n"] for r in con.execute("SELECT scope, COUNT(*) AS n FROM schedule GROUP BY scope")}
        scopes = sorted(_custom_scopes(con))
    return {"rulers": [{"scope": s, "label": scope_label(s), "blocks": counts.get(s, 0)} for s in scopes],
            "all_blocks": counts.get("all", 0)}


@app.put("/api/schedule", dependencies=[Depends(require_auth)])
async def save_schedule(request: Request):
    """Substitui a régua inteira (o painel sempre envia a lista completa).
    Sem `scope` no corpo, grava em "Todos os dias", como nas versões anteriores."""
    body = await request.json()
    scope = _check_scope(body.get("scope"))
    with db() as con:
        blocks = _write_ruler(con, scope, body.get("blocks", []))
        bump_version(con)
        con.commit()
    return {"scope": scope, "blocks": blocks}


@app.post("/api/schedule/copy", dependencies=[Depends(require_auth)])
async def copy_schedule(request: Request):
    """Copia uma régua para outras (ex.: "Repetir nos dias úteis": to = wd:1..wd:5).
    As réguas de destino são substituídas e passam a existir como réguas próprias.
    {"from": "all", "to": ["wd:1", ...]}  ou  {"from": ..., "to": [...], "blocks": [...]}
    para criar a partir de uma lista pronta (ex.: "a playlist X o dia todo")."""
    body = await request.json()
    targets = [_check_scope(t) for t in body.get("to", [])]
    if not targets:
        raise HTTPException(400, "Escolha pelo menos um dia de destino")
    with db() as con:
        if "blocks" in body:
            src = body["blocks"]
        else:
            frm = _check_scope(body.get("from"))
            custom = _custom_scopes(con)
            if frm != "all" and frm not in custom:   # copiar de régua herdada = copiar da que vale
                frm = ruler_for_day(_date.fromisoformat(frm[5:]), custom) if frm.startswith("date:") else "all"
            src = _blocks_of(con, frm)
        for t in targets:
            # id novo em cada cópia: o id de um bloco identifica o "slot" no ar
            _write_ruler(con, t, [dict(b, id=None) for b in src])
        bump_version(con)
        con.commit()
    return {"ok": True, "to": targets, "blocks": len(src)}


@app.delete("/api/schedule", dependencies=[Depends(require_auth)])
def delete_ruler(scope: str):
    """Apaga uma régua própria: o dia volta a seguir o nível de cima (dia da semana ou Todos os dias)."""
    scope = _check_scope(scope)
    if scope == "all":
        raise HTTPException(400, "A régua Todos os dias não pode ser removida (só esvaziada)")
    with db() as con:
        con.execute("DELETE FROM schedule WHERE scope=?", (scope,))
        con.execute("DELETE FROM rulers WHERE scope=?", (scope,))
        bump_version(con)
        con.commit()
    return {"ok": True}


@app.get("/api/calendar")
def calendar_month(month: str | None = None):
    """Panorama de um mês (?month=AAAA-MM): para cada dia, qual régua vale (e por quê),
    as playlists e itens agendados nela e o feriado nacional, se houver."""
    try:
        first = _date.fromisoformat((month or _date.today().strftime("%Y-%m")) + "-01")
    except ValueError:
        raise HTTPException(400, "Mês inválido (use AAAA-MM)")
    nxt = (first.replace(day=28) + _timedelta(days=4)).replace(day=1)
    hol = {}
    try:
        hol = {h["date"]: h["name"] for h in holidays(first.year)}
    except Exception:
        pass
    entries, _ = parse_curio(curio_text())
    with db() as con:
        custom = _custom_scopes(con)
        notices = [item_dict(r) for r in con.execute(
            "SELECT * FROM items WHERE playlist_id=? ORDER BY created_at", (NOTICE_PLAYLIST,))]
        pl_names = {r["id"]: r["name"] for r in con.execute("SELECT id, name FROM playlists")}
        it_names = {r["id"]: r["name"] for r in con.execute("SELECT id, name FROM items")}
        cache: dict[str, dict] = {}

        def summary(scope: str) -> dict:
            if scope not in cache:
                bs = _blocks_of(con, scope)
                pls, its = [], []
                for b in bs:
                    if b["kind"] == "playlist" and b["ref_id"] not in [p["id"] for p in pls]:
                        pls.append({"id": b["ref_id"], "name": pl_names.get(b["ref_id"], "?")})
                    if b["kind"] == "item" and b["ref_id"] not in [i["id"] for i in its]:
                        its.append({"id": b["ref_id"], "name": it_names.get(b["ref_id"], "?")})
                cache[scope] = {"playlists": pls, "items": its, "blocks": bs}
            return cache[scope]

        days, d = [], first
        while d < nxt:
            sc = ruler_for_day(d, custom)
            days.append({"date": d.isoformat(), "weekday": d.isoweekday(), "scope": sc,
                         "level": "date" if sc.startswith("date:") else "weekday" if sc.startswith("wd:") else "all",
                         "label": scope_label(sc), "holiday": hol.get(d.isoformat()),
                         "has_weekday_ruler": f"wd:{d.isoweekday()}" in custom,
                         # datas comemorativas da lista curada e avisos por data que aparecem no dia
                         **_day_dates(entries, d, hol.get(d.isoformat())),
                         "notices": [{"id": n["id"], "name": n["name"], "type": n["type"], "active": n["active"],
                                      "event": (occ := notice_occurrence(n["config"], d)).isoformat(),
                                      "days_left": (occ - d).days}
                                     for n in notices if notice_occurrence(n["config"], d)],
                         **summary(sc)})
            d += _timedelta(days=1)
    return {"month": first.strftime("%Y-%m"), "today": _date.today().isoformat(),
            "default_name": pl_names.get(DEFAULT_PLAYLIST, "Playlist padrão"), "days": days}


def _day_dates(entries: list[dict], d: _date, holiday: str | None) -> dict:
    """Datas da lista curada no dia. A que for o próprio feriado (mesmo nome, ex.: "Natal")
    não se repete: o texto dela vira o texto do feriado (holiday_text)."""
    on = [e for e in entries if _curio_matches(e["rule"], d)]
    same = [e for e in on if holiday and _stems(e["title"]) & _stems(holiday)]
    return {"dates": [{"title": e["title"], "text": e["text"]} for e in on if e not in same],
            "holiday_text": same[0]["text"] if same else None}


def _pick_block(blocks: list[dict], kind: str, now_min: int) -> dict | None:
    hits = [b for b in blocks if b["kind"] == kind and b["start_min"] <= now_min < b["end_min"]]
    if not hits:
        return None
    return max(hits, key=lambda b: (b["start_min"], -(b["end_min"] - b["start_min"])))


def resolve_now(con: sqlite3.Connection, now: datetime | None = None) -> dict:
    """Decide o que a TV deve exibir agora: escolhe a régua do dia (ruler_for_day) e aplica
    a regra de prioridade dentro dela (veja o comentário no topo desta seção).

    `slot` identifica a decisão: quando muda (ex.: deu 12:00 e entrou outro bloco, ou virou
    o dia e a régua é outra), o player interrompe o item atual e troca de conteúdo.
    """
    now = now or datetime.now()
    m = now.hour * 60 + now.minute
    scope = ruler_for_day(now.date(), _custom_scopes(con))
    blocks = _blocks_of(con, scope)
    names = {r["id"]: r["name"] for r in con.execute("SELECT id, name FROM playlists")}
    ruler = {"scope": scope, "label": scope_label(scope)}

    notices = notices_now(con, now)

    def items_of(pid: str) -> list[dict]:
        rows = con.execute("SELECT * FROM items WHERE playlist_id=? AND active=1 ORDER BY ord, created_at", (pid,))
        # Avisos por data do dia entram no fim da rotação (aparecem uma vez por volta da playlist)
        return [item_dict(r) for r in rows] + notices

    overlay = _pick_block(blocks, "item", m)
    if overlay:
        row = con.execute("SELECT * FROM items WHERE id=? AND active=1", (overlay["ref_id"],)).fetchone()
        if row:
            # Avisos por data também entram durante o item avulso: muita programação é feita só de
            # itens avulsos (ex.: Clima 10h–14h), e sem isso o aviso não apareceria no expediente.
            return {"slot": f"item:{overlay['id']}", "items": [item_dict(row)] + notices, "ruler": ruler,
                    "source": {"kind": "item", "name": row["name"], "until": _hhmm(overlay["end_min"])}}

    base = _pick_block(blocks, "playlist", m)
    if base:
        its = items_of(base["ref_id"])
        if len(its) > len(notices):   # playlist só com avisos = playlist vazia → cai na padrão
            return {"slot": f"playlist:{base['id']}", "items": its, "ruler": ruler,
                    "source": {"kind": "playlist", "name": names.get(base["ref_id"], "Playlist"),
                               "until": _hhmm(base["end_min"])}}

    upcoming = [b["start_min"] for b in blocks if b["start_min"] > m]
    return {"slot": "default", "items": items_of(DEFAULT_PLAYLIST), "ruler": ruler,
            "source": {"kind": "default", "name": names.get(DEFAULT_PLAYLIST, "Playlist padrão"),
                       "until": _hhmm(min(upcoming)) if upcoming else None}}


def current_state() -> dict:
    """O que a TV deve exibir agora + número de versão (usado pela rota HTTP e pelo WebSocket)."""
    with db() as con:
        state = resolve_now(con)
        ver = con.execute("SELECT val FROM version WHERE id=1").fetchone()
    state["version"] = ver["val"] if ver else 0
    state["server_time"] = datetime.now().strftime("%H:%M")
    state["skip"] = _skip_seq   # botão "Pular item" do painel (o player compara com o anterior)
    # Avisos por data intercalados agora: entram na assinatura do WebSocket para o player
    # receber a lista nova quando um aviso começa ou termina (ex.: início do horário de serviço)
    state["notices"] = [i["id"] for i in state["items"] if i.get("playlist_id") == NOTICE_PLAYLIST]
    # Curiosidades: quantos cartões há hoje (o player pula o item "today" se for 0) e as
    # regras das curiosidades automáticas, que o player intercala na playlist.
    try:
        state["today"] = {"count": today_info()["count"], "auto": today_auto_settings()}
    except Exception as e:
        print(f"[curiosidades] {e}")
        state["today"] = {"count": 0, "auto": {"enabled": False}}
    return state


@app.get("/api/player/state")
def player_state():
    return current_state()


# ─── Na TV agora / pular item (0.12.0) ────────────────────────────────────────
#
# O player avisa o que pôs na tela (POST /api/player/now, só do próprio computador) e o painel
# mostra em "Na TV agora" (GET /api/player/now). O botão "Pular item" (POST /api/player/skip)
# soma 1 em _skip_seq. Esse número vai no estado ("skip") e na assinatura do WebSocket, então
# o player recebe na hora, encerra o item atual e passa para o próximo da fila.
# Fica só na memória: reiniciar o servidor zera, o que é inofensivo.

_now_playing: dict = {}
_skip_seq = 0


@app.post("/api/player/now")
async def player_now_report(request: Request):
    if not request.client or request.client.host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(403, "Só o player deste computador informa o que está na tela")
    body = await request.json()
    if not body.get("name"):
        raise HTTPException(400, "Informe o item que está na tela")
    _now_playing.clear()
    _now_playing.update({k: body.get(k) for k in ("id", "name", "type", "duration", "source", "next", "skip_seq")})
    _now_playing["started"] = time.time()
    return {"ok": True}


@app.get("/api/player/now")
def player_now():
    """O que o player disse que está na tela e há quantos segundos ("stale" se faz tempo demais)."""
    if not _now_playing:
        return {"playing": False}
    elapsed = time.time() - _now_playing["started"]
    dur = int(_now_playing.get("duration") or 0)
    return {"playing": True, **_now_playing, "elapsed": round(elapsed, 1),
            "remaining": max(0, round(dur - elapsed)),
            # passou bem do tempo e o player não avisou o item seguinte: provavelmente está fechado
            "stale": elapsed > dur + 90, "players": len(_players)}


@app.post("/api/player/skip", dependencies=[Depends(require_auth)])
def player_skip():
    global _skip_seq
    _skip_seq += 1
    return {"ok": True, "skip": _skip_seq, "players": len(_players)}


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
    # "today" entra para o player saber na virada do dia (outras curiosidades) e quando as
    # curiosidades automáticas mudam em Configurações (que não alteram a versão).
    return (state.get("version"), state.get("slot"), json.dumps(state.get("today"), sort_keys=True),
            tuple(state.get("notices") or ()), state.get("skip"))


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
    # /api/player/now é o próprio player avisando o que pôs na tela: não muda a programação
    if (request.method in ("POST", "PUT", "DELETE") and request.url.path.startswith("/api/")
            and request.url.path != "/api/player/now"
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


# ─── Busca de imagens na web (Pexels ou Openverse) ───────────────────────────
#
# O painel pesquisa pelo NOME do item. O servidor só aceita importar imagens que ele mesmo
# devolveu numa busca recente (_img_allowed), então /api/image-import não vira um
# "baixador de qualquer endereço". A imagem escolhida é salva em data/uploads/: a TV
# continua mostrando mesmo sem internet e sem depender do site de origem.

IMG_IMPORT_MAX = 15 * 1024 * 1024
IMG_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
_img_allowed: dict[str, float] = {}   # url → quando apareceu numa busca


def _search_pexels(q: str, n: int) -> list[dict]:
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": q, "per_page": n, "locale": "pt-BR", "orientation": "landscape"})
    req = urllib.request.Request(url, headers={"Authorization": PEXELS_API_KEY, "User-Agent": "AlavaVision/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [{"thumb": p["src"]["medium"], "url": p["src"]["large2x"], "author": p.get("photographer", ""),
             "license": "Pexels", "link": p.get("url", ""), "source": "Pexels"} for p in data.get("photos", [])]


def _search_openverse(q: str, n: int) -> list[dict]:
    # license_type=commercial: só licenças que permitem uso em empresa; mature=false: sem conteúdo sensível.
    # Sem cadastro, o Openverse aceita no máximo 20 por página (acima disso responde 401).
    url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        {"q": q, "page_size": min(n, 20), "license_type": "commercial", "mature": "false"})
    data = _http_json(url, timeout=12)
    out = []
    for p in data.get("results", []):
        lic = f"CC {str(p.get('license', '')).upper()} {p.get('license_version') or ''}".strip()
        if p.get("license") in ("cc0", "pdm"):
            lic = "Domínio público"
        out.append({"thumb": p.get("thumbnail") or p.get("url"), "url": p.get("url"),
                    "author": p.get("creator") or "", "license": lic,
                    "link": p.get("foreign_landing_url") or "", "source": "Openverse"})
    return [x for x in out if x["url"]]


@app.get("/api/image-search", dependencies=[Depends(require_auth)])
def image_search(q: str, n: int = 24):
    q = q.strip()
    if len(q) < 2:
        raise HTTPException(400, "Dê um nome ao item antes de buscar (ele é usado como termo de busca)")
    n = max(4, min(40, n))
    source = "Pexels" if PEXELS_API_KEY else "Openverse"
    try:
        results = _search_pexels(q, n) if PEXELS_API_KEY else _search_openverse(q, n)
    except Exception as e:
        raise HTTPException(502, f"Falha ao buscar imagens no {source}: {e}")
    now = time.time()
    for k in [k for k, t in _img_allowed.items() if now - t > 3600]:
        _img_allowed.pop(k, None)
    for r in results:
        _img_allowed[r["url"]] = now
    return {"source": source, "results": results}


@app.post("/api/image-import", dependencies=[Depends(require_auth)])
async def image_import(request: Request):
    url = str((await request.json()).get("url", ""))
    if url not in _img_allowed:
        raise HTTPException(400, "Essa imagem não veio de uma busca recente. Busque de novo.")

    def fetch() -> tuple[bytes, str]:
        req = urllib.request.Request(url, headers={"User-Agent": "AlavaVision/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            ctype = r.headers.get_content_type()
            data = r.read(IMG_IMPORT_MAX + 1)
        return data, ctype

    try:
        data, ctype = await asyncio.to_thread(fetch)
    except Exception as e:
        raise HTTPException(502, f"Não consegui baixar a imagem: {e}")
    if ctype not in IMG_TYPES:
        raise HTTPException(400, f"O endereço não devolveu uma imagem ({ctype})")
    if len(data) > IMG_IMPORT_MAX:
        raise HTTPException(400, "Imagem maior que 15 MB")
    fname = f"{uuid.uuid4().hex[:12]}{IMG_TYPES[ctype]}"
    (UPLOADS_DIR / fname).write_bytes(data)
    return {"url": f"/uploads/{fname}", "type": "image"}


# ─── Notícias (RSS / Atom) ────────────────────────────────────────────────────
#
# Item "news": config.feeds = lista de endereços RSS/Atom. O servidor baixa cada feed
# (cache de 10 min por endereço, em paralelo), junta, tira repetidas e as que têm
# palavras de config.block_words, ordena da mais nova para a mais antiga e entrega até
# config.max_items manchetes para a tela /view/news/{id}.

NEWS_TTL = 600
_news_cache: dict[str, tuple[float, list[dict]]] = {}   # url → (quando, manchetes)
# Nome exibido da fonte quando o título do canal não ajuda (ex.: Agência Brasil manda "Feed Últimas")
NEWS_SOURCE_NAMES = {"agenciabrasil.ebc.com.br": "Agência Brasil", "feeds.bbci.co.uk": "BBC News Brasil",
                     "www.infomoney.com.br": "InfoMoney"}


def _local(tag: str) -> str:
    """'{http://search.yahoo.com/mrss/}content' → 'content'."""
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _strip_html(s: str) -> str:
    import re
    s = re.sub(r"<[^>]+>", " ", s or "")
    return " ".join(html.unescape(s).split())


def _parse_feed(data: bytes, url: str) -> list[dict]:
    import re
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    root = ET.fromstring(data)
    source = ""
    for el in root.iter():   # título do canal = nome da fonte
        if _local(el.tag) == "title" and (el.text or "").strip():
            source = _strip_html(el.text)
            break
    out = []
    for it in root.iter():
        if _local(it.tag) not in ("item", "entry"):
            continue
        f = {"title": "", "summary": "", "image": "", "ts": 0.0, "link": ""}
        for ch in it:
            name, text = _local(ch.tag), (ch.text or "").strip()
            if name == "title":
                f["title"] = _strip_html(text)
            elif name in ("subtitle", "summary") and not f["summary"]:
                f["summary"] = _strip_html(text)
            elif name == "description":
                if not f["image"]:
                    m = re.search(r'<img[^>]+src=["\']([^"\']+)', html.unescape(text))
                    if m:
                        f["image"] = m.group(1)
                f["_desc"] = _strip_html(text)
            elif name in ("content", "thumbnail") and ch.get("url") and ch.get("medium", "image") == "image":
                f["image"] = f["image"] if name == "thumbnail" and f["image"] else ch.get("url")
            elif name == "enclosure" and str(ch.get("type", "")).startswith("image") and not f["image"]:
                f["image"] = ch.get("url", "")
            elif name == "imagem-destaque" and text:
                f["image"] = text
            if "ichef.bbci.co.uk" in f["image"]:   # a BBC manda miniatura de 240 px; pede 800 px
                f["image"] = f["image"].replace("/ws/240/", "/ws/800/")
            elif name in ("pubDate", "published", "updated") and not f["ts"]:
                try:
                    f["ts"] = parsedate_to_datetime(text).timestamp()
                except (TypeError, ValueError):
                    try:
                        f["ts"] = datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
                    except ValueError:
                        pass
            elif name == "link":
                f["link"] = text or ch.get("href", "")
        if not f["summary"]:
            f["summary"] = f.get("_desc", "")
        f.pop("_desc", None)
        if len(f["summary"]) > 240:
            f["summary"] = f["summary"][:237].rsplit(" ", 1)[0] + "…"
        if f["title"]:
            host = urllib.parse.urlparse(url).hostname or ""
            f["source"] = NEWS_SOURCE_NAMES.get(host) or source or host
            out.append(f)
    return out


def _fetch_feed(url: str, force: bool = False) -> list[dict]:
    hit = _news_cache.get(url)
    if hit and not force and time.time() - hit[0] < NEWS_TTL:
        return hit[1]
    import gzip
    req = urllib.request.Request(url, headers={"User-Agent": "AlavaVision/1.0", "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read(5 * 1024 * 1024)
        if data[:2] == b"\x1f\x8b":          # alguns servidores mandam gzip mesmo sem pedir
            data = gzip.decompress(data)
        items = _parse_feed(data.lstrip(b"\xef\xbb\xbf \t\r\n"), url)
    except Exception:
        if hit:                  # sem internet: usa o que tinha
            return hit[1]
        raise
    _news_cache[url] = (time.time(), items)
    return items


def get_news(cfg: dict, force: bool = False) -> dict:
    import re
    from concurrent.futures import ThreadPoolExecutor
    feeds = [u.strip() for u in cfg.get("feeds", []) if str(u).strip().startswith(("http://", "https://"))][:12]
    # Cada palavra vale como INÍCIO de palavra: "assassin" pega "assassinato", mas
    # "morta" não pega "imortal" nem "comporta".
    words = [w.strip().lower() for w in str(cfg.get("block_words", "")).split(",") if w.strip()]
    block_re = re.compile(r"\b(" + "|".join(map(re.escape, words)) + ")") if words else None
    max_items = _num(cfg.get("max_items"), 15, 1, 60)
    items, errors = [], []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for url, res in zip(feeds, ex.map(lambda u: _try(_fetch_feed, u, force), feeds)):
            if isinstance(res, Exception):
                errors.append(f"{urllib.parse.urlparse(url).hostname}: {res}")
            else:
                items += res
    # "VÍDEOS: Jornal da Manhã…" e "EPTV 1 Campinas ao vivo" (g1) são listas de vídeos e
    # chamadas de transmissão: na TV viram um título sem conteúdo, então saem.
    # "VÍDEO: cratera engole caminhão" (singular) é notícia de verdade: só perde o prefixo.
    video_re = re.compile(r"^v[íi]deos\s*:|\bao vivo\s*$", re.I) if cfg.get("skip_videos", True) else None
    for it in items:
        it["title"] = re.sub(r"^v[íi]deo\s*:\s*", "", it["title"], flags=re.I)
    seen, out = set(), []
    for it in sorted(items, key=lambda x: -x["ts"]):
        key = it["title"].lower()
        text = (it["title"] + " " + it["summary"]).lower()
        if key in seen or (block_re and block_re.search(text)) or (video_re and video_re.search(it["title"])):
            continue
        seen.add(key)
        out.append(it)
        if len(out) >= max_items:
            break
    return {"items": out, "errors": errors, "updated_at": datetime.now().strftime("%H:%M")}


def _try(fn, *a):
    try:
        return fn(*a)
    except Exception as e:
        return e


@app.get("/api/news/{item_id}")
def api_news(item_id: str):
    return get_news(_item_config(item_id))


@app.post("/api/news-test", dependencies=[Depends(require_auth)])
async def api_news_test(request: Request):
    """Painel: testa os feeds digitados antes de salvar (mostra quantas manchetes e os erros)."""
    return await asyncio.to_thread(get_news, await request.json())


# ─── Curiosidades e datas ("Hoje é Dia de…") ─────────────────────────────────
#
# Duas fontes, as duas previsíveis (decisão de 18/11/2026: nada de "neste dia" da Wikipedia,
# que mistura tragédias):
#   • lista curada em data/datas_comemorativas.txt (copiada de conteudo/ na 1ª vez, editável no painel);
#   • feriados nacionais da BrasilAPI, guardados em data/feriados_AAAA.json (funciona sem internet depois).
# today_info() monta os "cartões" do dia: datas da lista; senão o feriado de hoje; e, se faltar
# pouco para um feriado, um aviso "Faltam N dias". O item "today" e as curiosidades automáticas
# (Configurações) usam a mesma tela /view/today.

CURIO_DEFAULT = BASE / "conteudo" / "datas_comemorativas.txt"
CURIO_FILE = DATA_DIR / "datas_comemorativas.txt"
WEEKDAYS_PT = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
MONTHS_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
             "setembro", "outubro", "novembro", "dezembro"]


def curio_text() -> str:
    if not CURIO_FILE.exists() and CURIO_DEFAULT.exists():
        CURIO_FILE.write_text(CURIO_DEFAULT.read_text(encoding="utf-8"), encoding="utf-8")
    return CURIO_FILE.read_text(encoding="utf-8") if CURIO_FILE.exists() else ""


def parse_curio(text: str) -> tuple[list[dict], list[str]]:
    """Linhas "quando | título | texto" → (datas, erros com o número da linha)."""
    import re
    out, errors = [], []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2 or not parts[1]:
            errors.append(f"linha {n}: use  data | título | texto")
            continue
        when, title, body = parts[0].lower(), parts[1], " | ".join(parts[2:])
        e = {"title": title, "text": body}
        if m := re.fullmatch(r"(\d{1,2})/(\d{1,2})", when):
            d, mo = int(m[1]), int(m[2])
            try:
                datetime(2024, mo, d)   # 2024 é bissexto: aceita 29/02
            except ValueError:
                errors.append(f"linha {n}: data inválida '{parts[0]}'")
                continue
            e["rule"] = ("dm", d, mo)
        elif m := re.fullmatch(r"(\d|último|ultimo)\s*[ºª°oa]?\s*(\w+?)(?:-feira)?\s*/\s*(\d{1,2})", when):
            plain = lambda s: s.replace("á", "a").replace("ç", "c")   # "sabado" = "sábado", "terca" = "terça"
            wd = next((i for i, w in enumerate(WEEKDAYS_PT) if plain(w).startswith(plain(m[2])[:3])), None)
            nth = -1 if m[1].startswith("ú") or m[1].startswith("u") else int(m[1])
            if wd is None or not 1 <= int(m[3]) <= 12 or nth == 0 or nth > 5:
                errors.append(f"linha {n}: não entendi '{parts[0]}' (ex.: 2º domingo/05)")
                continue
            e["rule"] = ("nth", nth, wd, int(m[3]))
        elif m := re.fullmatch(r"dia\s+(\d{1,3})", when):
            e["rule"] = ("yday", int(m[1]))
        else:
            errors.append(f"linha {n}: não entendi a data '{parts[0]}' (use DD/MM, 2º domingo/05 ou dia 256)")
            continue
        out.append(e)
    return out, errors


def _curio_matches(rule: tuple, day) -> bool:
    import calendar
    kind = rule[0]
    if kind == "dm":
        return day.day == rule[1] and day.month == rule[2]
    if kind == "yday":
        return day.timetuple().tm_yday == rule[1]
    _, nth, wd, month = rule
    if day.month != month or day.weekday() != wd:
        return False
    if nth == -1:
        return day.day + 7 > calendar.monthrange(day.year, month)[1]
    return (day.day - 1) // 7 + 1 == nth


_hol_failed: dict[int, float] = {}   # ano → quando a BrasilAPI falhou (tenta de novo depois de 1 h)


def holidays(year: int) -> list[dict]:
    cache = DATA_DIR / f"feriados_{year}.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text(encoding="utf-8"))
        except ValueError:
            pass
    # Sem internet, não tenta a cada consulta (cada tentativa espera até 8 s).
    if time.time() - _hol_failed.get(year, 0) < 3600:
        return []
    try:
        data = _http_json(f"https://brasilapi.com.br/api/feriados/v1/{year}", timeout=8)
        cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data
    except Exception as e:
        _hol_failed[year] = time.time()
        print(f"[curiosidades] feriados de {year} indisponíveis: {e}")
        return []


TODAY_SOON_DAYS = 15   # aviso "Faltam N dias para o feriado" a partir de 15 dias antes


def _stems(s: str) -> set[str]:
    """Radicais de 5 letras das palavras de 4+ letras: "Dia do Trabalhador" ~ "Dia do trabalho"."""
    import re
    return {w[:5] for w in re.findall(r"\w+", s.lower()) if len(w) >= 4}


def today_info(day=None) -> dict:
    from datetime import date, timedelta
    day = day or date.today()
    entries, _ = parse_curio(curio_text())
    on = lambda d: [e for e in entries if _curio_matches(e["rule"], d)]
    cards = [{"kind": "date", "eyebrow": "Hoje é", "title": e["title"], "text": e["text"]} for e in on(day)]
    hol = {h["date"]: h["name"] for h in holidays(day.year) + holidays(day.year + 1)}
    today_hol = hol.get(day.isoformat())
    # Feriado de hoje: aparece, a não ser que a lista já tenha a mesma data com outro nome
    # (20/11 "Dia de Zumbi e da Consciência Negra" = "Dia da consciência negra").
    # Em 12/10 aparecem os dois: "Dia das Crianças" (lista) e "Nossa Senhora Aparecida" (feriado).
    if today_hol and not any(_stems(e["title"]) & _stems(today_hol) for e in on(day)):
        cards.insert(0, {"kind": "holiday", "eyebrow": "Hoje é feriado", "title": today_hol, "text": "Bom descanso!"})
    for i in range(1, TODAY_SOON_DAYS + 1):
        d = day + timedelta(days=i)
        if d.isoformat() in hol:
            if hol[d.isoformat()] == today_hol:   # Carnaval segunda → terça: é o mesmo feriado
                break
            named = on(d)   # nome da lista, se houver ("Dia de Zumbi…" em vez de "Dia da consciência negra")
            title = next((e["title"] for e in named if _stems(e["title"]) & _stems(hol[d.isoformat()])), hol[d.isoformat()])
            when = "Amanhã é feriado" if i == 1 else f"Faltam {i} dias para o feriado"
            cards.append({"kind": "soon", "eyebrow": when, "title": title,
                          "text": f"{WEEKDAYS_PT[d.weekday()].capitalize()}{'-feira' if d.weekday() < 5 else ''}, "
                                  f"{d.day} de {MONTHS_PT[d.month - 1]}."})
            break
    label = f"{WEEKDAYS_PT[day.weekday()]}{'-feira' if day.weekday() < 5 else ''}, {day.day} de {MONTHS_PT[day.month - 1]}"
    return {"date": day.isoformat(), "label": label, "cards": cards, "count": len(cards)}


def today_auto_settings() -> dict:
    """Curiosidades automáticas (Configurações): o player intercala a tela /view/today na playlist."""
    s = load_settings()
    return {"enabled": s.get("today_auto") == "1", "start": s.get("today_start") or "08:00",
            "end": s.get("today_end") or "18:00", "every_min": _num(s.get("today_every"), 30, 5, 240),
            "duration": _num(s.get("today_duration"), 15, 5, 120)}


# ─── Avisos por data (0.11.0) ─────────────────────────────────────────────────
#
# Um aviso é um item comum (mensagem, imagem, contador ou "Hoje é dia") guardado na playlist
# reservada NOTICE_PLAYLIST ("Avisos por data", que não aparece nas listas do painel), com
#   config.notice = {"date": "AAAA-MM-DD",   dia do evento
#                    "days_before": 0,       começa a aparecer N dias antes (contagem regressiva)
#                    "yearly": false,        repete todo ano
#                    "anchor": {"holiday": "Carnaval"} | {"curio": "Dia das Mães"} | {},
#                    "hours": "all" | "work"}   o dia todo ou só no horário de serviço
#
# Na TV, o aviso é INTERCALADO: entra no fim da rotação do que estiver no ar (resolve_now),
# sem mexer na programação do dia. Vale também durante um item avulso agendado: ele passa a
# alternar com os avisos do dia (ex.: Clima, Aviso, Clima, Aviso...).
# Repetir todo ano: com "anchor", a data acompanha o feriado ou a data móvel da lista
# (Carnaval, Páscoa, Dia das Mães...); sem ela, repete o mesmo DD/MM.

NOTICE_PLAYLIST = "avisos"
NOTICE_TYPES = {"message", "image", "countdown", "today"}


def _curio_day(title: str, year: int) -> _date | None:
    """Dia do ano `year` em que cai a data da lista curada com esse título (datas móveis)."""
    entries, _ = parse_curio(curio_text())
    rules = [e["rule"] for e in entries if e["title"].lower() == title.lower()]
    if not rules:
        return None
    d = _date(year, 1, 1)
    while d.year == year:
        if any(_curio_matches(r, d) for r in rules):
            return d
        d += _timedelta(days=1)
    return None


def notice_date(n: dict, year: int) -> _date | None:
    """Dia do evento do aviso no ano `year` (None se o aviso não acontece nesse ano)."""
    try:
        base = _date.fromisoformat(str(n.get("date", "")))
    except ValueError:
        return None
    if not n.get("yearly"):
        return base if base.year == year else None
    a = n.get("anchor") or {}
    if a.get("holiday"):
        # Feriado de vários dias com o mesmo nome (Carnaval segunda e terça): segue o mesmo dia
        # (o 1º ou o 2º) em que o aviso foi criado.
        same = lambda y: sorted(h["date"] for h in holidays(y) if h["name"] == a["holiday"])
        orig, hits = same(base.year), same(year)
        if hits:
            k = orig.index(base.isoformat()) if base.isoformat() in orig else 0
            return _date.fromisoformat(hits[min(k, len(hits) - 1)])
    if a.get("curio"):
        hit = _curio_day(a["curio"], year)
        if hit:
            return hit
    try:
        return base.replace(year=year)
    except ValueError:            # 29/02 em ano que não é bissexto
        return base.replace(year=year, day=28)


def notice_occurrence(cfg: dict, day: _date) -> _date | None:
    """Se o aviso deve aparecer no dia `day`, devolve o dia do evento correspondente."""
    n = cfg.get("notice") or {}
    before = _num(n.get("days_before"), 0, 0, 60)
    for y in (day.year, day.year + 1):      # +1: contagem de 28/12 para um evento em janeiro
        d = notice_date(n, y)
        if d and d - _timedelta(days=before) <= day <= d:
            return d
    return None


def notices_now(con: sqlite3.Connection, now: datetime) -> list[dict]:
    """Avisos que a TV intercala agora (dia certo e, se for o caso, horário de serviço)."""
    rows = con.execute("SELECT * FROM items WHERE playlist_id=? AND active=1 ORDER BY ord, created_at",
                       (NOTICE_PLAYLIST,)).fetchall()
    if not rows:
        return []
    hhmm, work = now.strftime("%H:%M"), None
    out = []
    for r in rows:
        it = item_dict(r)
        if not notice_occurrence(it["config"], now.date()):
            continue
        if (it["config"].get("notice") or {}).get("hours") == "work":
            work = work or today_auto_settings()
            if not work["start"] <= hhmm < work["end"]:
                continue
        out.append(it)
    return out


@app.get("/api/notices")
def list_notices():
    """Todos os avisos cadastrados (o calendário mostra os de cada dia em /api/calendar)."""
    with db() as con:
        rows = [item_dict(r) for r in con.execute(
            "SELECT * FROM items WHERE playlist_id=? ORDER BY created_at", (NOTICE_PLAYLIST,))]
    return {"notices": rows}


@app.get("/api/today")
def api_today(d: str | None = None):
    from datetime import date
    try:
        day = date.fromisoformat(d) if d else None
    except ValueError:
        raise HTTPException(400, "Data inválida (use AAAA-MM-DD)")
    return today_info(day)


@app.get("/api/curiosities", dependencies=[Depends(require_auth)])
def get_curiosities():
    return {"text": curio_text()}


@app.put("/api/curiosities", dependencies=[Depends(require_auth)])
async def save_curiosities(request: Request):
    text = str((await request.json()).get("text", ""))
    entries, errors = parse_curio(text)
    if errors:
        raise HTTPException(400, "Corrija antes de salvar: " + "; ".join(errors[:5]))
    CURIO_FILE.write_text(text, encoding="utf-8")
    with db() as con:
        bump_version(con)
        con.commit()
    return {"ok": True, "count": len(entries)}


@app.post("/api/curiosities/reset", dependencies=[Depends(require_auth)])
def reset_curiosities():
    """Volta para a lista que vem com o sistema (conteudo/datas_comemorativas.txt)."""
    CURIO_FILE.write_text(CURIO_DEFAULT.read_text(encoding="utf-8"), encoding="utf-8")
    return {"text": curio_text()}


# ─── Voz (Piper, offline) ─────────────────────────────────────────────────────
#
# Mensagem com config.speak: a tela toca /api/tts/{id}.wav ao abrir. O áudio é gerado pelo
# Piper (ferramentas/piper/, instalado por ferramentas/instalar_voz.py ou pelo painel) e
# guardado em data/tts/<hash>.wav: o mesmo texto com a mesma voz e velocidade não é gerado
# de novo. Sem o Piper instalado, a rota responde 404 e a mensagem aparece sem som.

TTS_DIR = DATA_DIR / "tts"
PIPER_DIR = BASE / "ferramentas" / "piper"
PIPER_EXE = PIPER_DIR / "piper.exe"
TTS_RATES = {"slow": 1.35, "normal": 1.0, "fast": 0.8}   # length_scale do Piper: maior = mais devagar
_tts_lock = threading.Lock()
_tts_install: dict = {"running": False, "log": [], "ok": None}


def tts_voices() -> list[str]:
    d = PIPER_DIR / "vozes"
    return sorted(p.name.split("-")[1] for p in d.glob("pt_BR-*.onnx")
                  if p.with_suffix(".onnx.json").exists()) if d.exists() else []


def tts_wav(text: str, voice: str = "", rate: str = "normal") -> Path:
    """Gera (ou reaproveita) o .wav do texto. Erro claro se o Piper não estiver instalado."""
    import hashlib
    import subprocess
    voices = tts_voices()
    if not PIPER_EXE.exists() or not voices:
        raise HTTPException(404, "Voz não instalada (Configurações → Voz → Instalar voz)")
    voice = voice if voice in voices else ("faber" if "faber" in voices else voices[0])
    scale = TTS_RATES.get(rate, 1.0)
    text = " ".join(str(text).split())[:1500]
    if not text:
        raise HTTPException(400, "Nada para ler")
    key = hashlib.sha1(f"{voice}|{scale}|{text}".encode("utf-8")).hexdigest()[:20]
    out = TTS_DIR / f"{key}.wav"
    if out.exists():
        return out
    import wave
    TTS_DIR.mkdir(parents=True, exist_ok=True)
    model = next((PIPER_DIR / "vozes").glob(f"pt_BR-{voice}-*.onnx"))
    rate_hz = json.loads(model.with_suffix(".onnx.json").read_text(encoding="utf-8"))["audio"]["sample_rate"]
    # O piper.exe de 2023 quebra (0xC0000409) com acento no caminho, ex.: C:\Users\Maurício\...
    # Por isso roda DENTRO da pasta do Piper, com caminhos relativos, e devolve o áudio cru pela
    # saída padrão; quem grava o .wav (em qualquer caminho) é o Python.
    with _tts_lock:   # um de cada vez: o Piper usa bastante CPU
        r = subprocess.run([str(PIPER_EXE), "--model", f"vozes/{model.name}", "--espeak_data", "espeak-ng-data",
                            "--output_raw", "--length_scale", str(scale), "--sentence_silence", "0.35"],
                           input=text.encode("utf-8"), capture_output=True, timeout=120, cwd=str(PIPER_DIR),
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode != 0 or not r.stdout:
        err = r.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] or [f"código {r.returncode}"]
        raise HTTPException(500, f"Piper falhou: {err[0]}")
    tmp = out.with_suffix(".tmp")
    with wave.open(str(tmp), "wb") as w:   # áudio cru do Piper: 16 bits, mono
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate_hz)
        w.writeframes(r.stdout)
    tmp.replace(out)
    return out


def _speech_text(cfg: dict) -> str:
    """O que a mensagem fala: o texto próprio de leitura, se houver; senão título + texto."""
    custom = str(cfg.get("speak_text") or "").strip()
    if custom:
        return custom
    title, text = str(cfg.get("title") or "").strip(), str(cfg.get("text") or "").strip()
    # O ponto depois do título faz o Piper dar uma pausa antes do texto.
    return f"{title.rstrip('.!?:')}. {text}" if title and text else (title or text)


@app.get("/api/tts/{item_id}.wav")
def api_tts_item(item_id: str):
    cfg = _item_config(item_id)
    path = tts_wav(_speech_text(cfg), cfg.get("speak_voice", ""), cfg.get("speak_rate", "normal"))
    return FileResponse(str(path), media_type="audio/wav", headers={"Cache-Control": "no-store"})


@app.post("/api/tts-preview", dependencies=[Depends(require_auth)])
async def api_tts_preview(request: Request):
    """Painel: botão "Ouvir" do formulário de mensagem (gera sem salvar o item)."""
    cfg = await request.json()
    path = await asyncio.to_thread(tts_wav, _speech_text(cfg), cfg.get("speak_voice", ""), cfg.get("speak_rate", "normal"))
    return FileResponse(str(path), media_type="audio/wav")


@app.get("/api/tts-status")
def api_tts_status():
    return {"installed": PIPER_EXE.exists() and bool(tts_voices()), "voices": tts_voices(),
            "available": ["faber", "cadu", "jeff"], "windows": os.name == "nt",
            "install": {k: (v[-12:] if k == "log" else v) for k, v in _tts_install.items()}}


@app.post("/api/tts-install", dependencies=[Depends(require_auth)])
async def api_tts_install(request: Request):
    """Baixa o Piper + a voz escolhida em segundo plano (ferramentas/instalar_voz.py)."""
    import subprocess
    voice = str((await request.json()).get("voice", "faber"))
    if voice not in ("faber", "cadu", "jeff"):
        raise HTTPException(400, "Voz desconhecida")
    if _tts_install["running"]:
        raise HTTPException(409, "A instalação já está em andamento")

    def run():
        _tts_install.update(running=True, log=[], ok=None)
        import sys
        try:
            p = subprocess.Popen([sys.executable, str(BASE / "ferramentas" / "instalar_voz.py"), "--voz", voice],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=str(BASE),
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            for line in p.stdout:
                _tts_install["log"].append(line.decode("utf-8", "replace").rstrip())
            _tts_install["ok"] = p.wait() == 0
        except Exception as e:
            _tts_install["log"].append(f"Erro: {e}")
            _tts_install["ok"] = False
        finally:
            _tts_install["running"] = False

    threading.Thread(target=run, name="instalar-voz", daemon=True).start()
    return {"started": True}


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
        _warm_news()
        time.sleep(WX_REFRESH_EVERY)


def _warm_news():
    """Deixa as manchetes dos itens de notícias ativos em cache (a tela abre sem esperar a internet)."""
    try:
        with db() as con:
            rows = con.execute("SELECT config FROM items WHERE type='news' AND active=1").fetchall()
        for r in rows:
            get_news(json.loads(r["config"] or "{}"), force=True)
    except Exception as e:
        print(f"[notícias] falha ao atualizar em segundo plano: {e}")


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
    # Aviso por data que repete todo ano: o contador aponta para o evento deste ano
    if cfg.get("notice") and (occ := notice_occurrence(cfg, _date.today())):
        cfg["target"] = occ.isoformat() + (str(cfg.get("target", ""))[10:] or "T00:00")
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


@app.get("/view/today")
def view_today(d: str | None = None, per: int = 0):
    """Tela "Hoje é Dia de…". Vários cartões no dia: troca entre eles a cada `per` segundos
    (padrão: 8). `?d=AAAA-MM-DD` mostra outro dia, para testar pelo painel.
    """
    info = api_today(d)
    data = json.dumps(info, ensure_ascii=False).replace("</", "<\\/")
    per_ms = _num(per, 8, 3, 60) * 1000
    return view_html(f"""
<style>
  .td{{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
    padding:8vh 8vw;gap:3.4vh;color:#fff;transition:background 1s ease}}
  .td.date{{background:radial-gradient(120% 120% at 20% 10%,#1e40af 0%,#0b1120 70%)}}
  .td.holiday{{background:radial-gradient(120% 120% at 20% 10%,#047857 0%,#052e16 72%)}}
  .td.soon{{background:radial-gradient(120% 120% at 20% 10%,#b45309 0%,#1c1206 72%)}}
  .ico{{font-size:11vh;line-height:1}}
  .eyebrow{{font-size:3.4vh;font-weight:700;letter-spacing:.35em;text-transform:uppercase;opacity:.8}}
  .title{{font-size:9vh;font-weight:800;line-height:1.08;max-width:84vw}}
  .text{{font-size:3.6vh;line-height:1.4;max-width:70vw;opacity:.88}}
  .when{{position:fixed;bottom:5vh;left:0;right:0;text-align:center;font-size:2.6vh;opacity:.55;letter-spacing:.06em}}
  .fade{{animation:f .8s ease both}} @keyframes f{{from{{opacity:0;transform:translateY(3vh)}}to{{opacity:1;transform:none}}}}
</style>
<div class="td date" id="td"><div class="ico" id="ico"></div><div class="eyebrow" id="eb"></div>
  <div class="title" id="tt"></div><div class="text" id="tx"></div></div>
<div class="when" id="when"></div>
<script>
const I = {data}, ICON = {{date: '📅', holiday: '🎉', soon: '⏳'}};
const $ = id => document.getElementById(id);
$('when').textContent = I.label;
let k = 0;
function show() {{
  const c = I.cards[k % Math.max(1, I.cards.length)] ||
            {{kind: 'date', eyebrow: 'Hoje', title: I.label, text: 'Nenhuma data especial cadastrada para hoje.'}};
  $('td').className = 'td ' + c.kind;
  for (const [id, v] of [['ico', ICON[c.kind]], ['eb', c.eyebrow], ['tt', c.title], ['tx', c.text]]) {{
    const el = $(id); el.textContent = v || ''; el.classList.remove('fade'); void el.offsetWidth; el.classList.add('fade');
  }}
  k++;
}}
show(); if (I.cards.length > 1) setInterval(show, {per_ms});
</script>""")


@app.get("/view/news/{item_id}")
def view_news(item_id: str):
    """Tela de notícias: uma manchete por vez (foto + título + resumo), trocando a cada
    config.per_headline segundos. Começa já com as manchetes embutidas (sem "Carregando…")
    e atualiza sozinha a cada 5 min. Guarda no navegador da TV em qual manchete parou,
    para a próxima vez que o item entrar continuar dali em vez de repetir as primeiras.
    """
    cfg = _item_config(item_id)
    data = json.dumps(get_news(cfg), ensure_ascii=False).replace("</", "<\\/")
    title = html.escape(str(cfg.get("title") or "Notícias"))
    accent = _css_color(cfg.get("accent"), "#38bdf8")
    per = _num(cfg.get("per_headline"), 9, 4, 60)
    show_img = "true" if cfg.get("show_images", True) else "false"
    # Logo Alava no cabeçalho (0.11.0; config.show_logo, ligado por padrão).
    # Usa assets/watermark.png (versão branca, fundo transparente): é a de melhor contraste
    # no fundo azul-escuro desta tela. As outras (minimalista azul-marinho e "fundo branco")
    # sumiriam no fundo escuro. Mesmo tamanho do logo das telas de clima e trânsito.
    logo = ('<img class="logo" src="/assets/watermark.png" alt="Alava"><span class="sep"></span>'
            if cfg.get("show_logo", True) else "")
    return HTMLResponse(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:100%;height:100%;overflow:hidden;background:#0b1120;color:#f1f5f9;font-family:'Segoe UI',system-ui,sans-serif}}
.top{{position:fixed;top:0;left:0;right:0;height:11vh;display:flex;align-items:center;justify-content:space-between;padding:0 4vw}}
.top h1{{font-size:3.4vh;font-weight:700;letter-spacing:.32em;text-transform:uppercase;color:{accent}}}
/* Logo Alava: à esquerda do título, separada por um traço fino na cor de destaque.
   Altura igual à do logo do clima/trânsito (4,2% da tela, mínimo 26 px) e leve transparência
   para não competir com a manchete. Fica no cabeçalho, fora da área do cartão. */
.top .brand{{display:flex;align-items:center;gap:1.6vw}}
.top .logo{{height:clamp(26px,4.2vh,72px);width:auto;opacity:.9;display:block}}
.top .sep{{width:2px;height:4.4vh;border-radius:2px;background:{accent};opacity:.55}}
.top .clock{{font-size:4.2vh;font-weight:300;font-variant-numeric:tabular-nums;opacity:.85}}
.card{{position:fixed;top:13vh;bottom:12vh;left:4vw;right:4vw;display:grid;grid-template-columns:46% 1fr;gap:4vw;align-items:center;
  transition:opacity .6s ease}}
.card.noimg{{grid-template-columns:1fr}}
.card.out{{opacity:0}}
.pic{{width:100%;height:100%;border-radius:2.2vh;background:#1e293b center/cover no-repeat;box-shadow:0 3vh 7vh rgba(0,0,0,.45)}}
.card.noimg .pic{{display:none}}
.meta{{font-size:2.4vh;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:{accent};margin-bottom:2.6vh}}
.headline{{font-size:6vh;font-weight:700;line-height:1.14;display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}}
.card.noimg .headline{{font-size:7.6vh}}
.summary{{margin-top:3vh;font-size:3vh;line-height:1.4;color:#cbd5e1;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}}
.bottom{{position:fixed;left:4vw;right:4vw;bottom:4.5vh;display:flex;align-items:center;gap:2vw;font-size:2.2vh;color:#94a3b8;
  font-variant-numeric:tabular-nums}}
.bar{{flex:1;height:.6vh;border-radius:1vh;background:rgba(148,163,184,.25);overflow:hidden}}
.bar i{{display:block;height:100%;width:0;background:{accent}}}
.empty{{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;font-size:4vh;color:#94a3b8;text-align:center}}
</style></head>
<body>
<div class="top"><div class="brand">{logo}<h1>{title}</h1></div><div class="clock" id="clock"></div></div>
<div class="card" id="card"><div class="pic" id="pic"></div>
  <div><div class="meta" id="meta"></div><div class="headline" id="headline"></div><div class="summary" id="summary"></div></div></div>
<div class="bottom"><span id="count"></span><div class="bar"><i id="bar"></i></div></div>
<script>
let N = {data};
const PER = {per} * 1000, SHOW_IMG = {show_img}, KEY = 'news-idx-{html.escape(item_id)}';
const $ = id => document.getElementById(id);
const pad = n => String(n).padStart(2, '0');
function tick() {{ const d = new Date(); $('clock').textContent = pad(d.getHours()) + ':' + pad(d.getMinutes()); }}
tick(); setInterval(tick, 1000);
function ago(ts) {{
  if (!ts) return '';
  const m = Math.max(0, Math.round((Date.now() / 1000 - ts) / 60));
  if (m < 60) return m <= 1 ? 'agora' : `há ${{m}} min`;
  const h = Math.round(m / 60); return h < 24 ? `há ${{h}} h` : `há ${{Math.round(h / 24)}} d`;
}}
let idx = 0;
try {{ idx = parseInt(localStorage.getItem(KEY)) || 0; }} catch (e) {{}}
function show() {{
  const list = (N && N.items) || [];
  if (!list.length) {{
    document.body.insertAdjacentHTML('beforeend', '<div class="empty">Sem notícias no momento.<br>Confira os endereços dos feeds no painel.</div>');
    $('card').hidden = true; return;
  }}
  idx %= list.length;
  const it = list[idx];
  $('card').classList.add('out');
  setTimeout(() => {{
    const img = SHOW_IMG && it.image;
    $('card').classList.toggle('noimg', !img);
    $('pic').style.backgroundImage = img ? `url("${{it.image.replace(/"/g, '%22')}}")` : '';
    $('meta').textContent = [it.source, ago(it.ts)].filter(Boolean).join('  ·  ');
    $('headline').textContent = it.title;
    $('summary').textContent = it.summary;
    $('count').textContent = `${{idx + 1}} / ${{list.length}}`;
    const bar = $('bar'); bar.style.transition = 'none'; bar.style.width = '0';
    requestAnimationFrame(() => requestAnimationFrame(() => {{ bar.style.transition = `width ${{PER}}ms linear`; bar.style.width = '100%'; }}));
    $('card').classList.remove('out');
    try {{ localStorage.setItem(KEY, (idx + 1) % list.length); }} catch (e) {{}}
    idx++;
  }}, 450);
}}
show(); setInterval(show, PER);
setInterval(async () => {{ try {{ N = await (await fetch('/api/news/{html.escape(item_id)}')).json(); }} catch (e) {{}} }}, 300000);
</script>
</body></html>""", headers={"Cache-Control": "no-store"})


MSG_FONTS = {   # fontes que já vêm no Windows (o PC da TV não precisa de internet para elas)
    "sans": "'Segoe UI',system-ui,sans-serif",
    "serif": "Georgia,'Times New Roman',serif",
    "impact": "Impact,'Arial Black',sans-serif",
    "hand": "'Segoe Print','Comic Sans MS',cursive",
    "mono": "Consolas,'Courier New',monospace",
}
MSG_ANIMS = {
    "none": "",
    "fade": "@keyframes in{from{opacity:0}to{opacity:1}}",
    "zoom": "@keyframes in{from{opacity:0;transform:scale(.85)}to{opacity:1;transform:none}}",
    "slide": "@keyframes in{from{opacity:0;transform:translateY(8vh)}to{opacity:1;transform:none}}",
}


def _css_color(value, default: str) -> str:
    """Aceita só #rgb/#rrggbb (o valor vai direto para o CSS)."""
    v = str(value or "")
    return v if len(v) in (4, 7) and v.startswith("#") and all(c in "0123456789abcdefABCDEF" for c in v[1:]) else default


def _num(value, default, lo, hi):
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


@app.get("/view/message/{item_id}")
def view_message(item_id: str):
    return _render_message(_item_config(item_id), item_id)


@app.get("/view/message-preview")
def view_message_preview(c: str = "{}"):
    """Prévia ao vivo do formulário do painel: recebe a config em JSON (?c=...), sem salvar nada."""
    try:
        cfg = json.loads(c)
    except ValueError:
        cfg = {}
    if not isinstance(cfg, dict):
        cfg = {}
    cfg["speak"] = False   # a prévia não fala
    return _render_message(cfg, None)


def _render_message(cfg: dict, item_id: str | None) -> HTMLResponse:
    """Mensagem de texto. Campos de config (todos opcionais, com o padrão da 0.9.0):

    text, title ............ texto principal e título acima dele (quebras de linha são mantidas)
    bg_mode ................ "solid" (bg_color) | "gradient" (bg_color → bg_color2, bg_angle) | "image"
    bg_image, bg_dim ....... imagem de fundo e escurecimento por cima (0–85 %) para o texto ler bem
    bg_credit .............. crédito da foto (busca na web), no canto inferior direito
    text_color, font_size, font_family (MSG_FONTS), bold, align, shadow, animation (MSG_ANIMS)
    show_clock ............. relógio acima do texto
    speak .................. ler o texto em voz alta (Piper, 0.10.0+)
    """
    nl2br = lambda s: html.escape(str(s or "")).replace("\n", "<br>")
    text, title = nl2br(cfg.get("text")), nl2br(cfg.get("title"))
    bg = _css_color(cfg.get("bg_color"), "#0a0a1a")
    bg2 = _css_color(cfg.get("bg_color2"), "#1e3a8a")
    fg = _css_color(cfg.get("text_color"), "#ffffff")
    size = _num(cfg.get("font_size"), 72, 20, 300)
    angle = _num(cfg.get("bg_angle"), 135, 0, 360)
    dim = _num(cfg.get("bg_dim"), 40, 0, 85)
    mode = cfg.get("bg_mode") or "solid"
    img = str(cfg.get("bg_image") or "")
    if mode == "image" and img.startswith("/uploads/"):
        background = f"#000 url('{html.escape(img)}') center/cover no-repeat"
        overlay = f"<div style='position:absolute;inset:0;background:rgba(0,0,0,{dim / 100})'></div>"
    elif mode == "gradient":
        background, overlay = f"linear-gradient({angle}deg,{bg},{bg2})", ""
    else:
        background, overlay = bg, ""
    font = MSG_FONTS.get(cfg.get("font_family"), MSG_FONTS["sans"])
    weight = 700 if cfg.get("bold", True) else 400
    align = cfg.get("align") if cfg.get("align") in ("left", "center", "right") else "center"
    flex_align = {"left": "flex-start", "center": "center", "right": "flex-end"}[align]
    shadow = "text-shadow:0 .4vh 2.4vh rgba(0,0,0,.55);" if cfg.get("shadow", mode == "image") else ""
    anim_name = cfg.get("animation") if cfg.get("animation") in MSG_ANIMS else "none"
    anim_css = MSG_ANIMS[anim_name]
    anim_use = "animation:in 1.1s cubic-bezier(.2,.7,.2,1) both;" if anim_css else ""
    show_clock = "true" if cfg.get("show_clock", True) else "false"
    credit = html.escape(str(cfg.get("bg_credit") or "")) if mode == "image" else ""
    audio = (f'<audio src="/api/tts/{html.escape(item_id)}.wav" autoplay></audio>'
             if cfg.get("speak") and item_id else "")
    return view_html(f"""
<style>{anim_css}</style>
<div style="position:fixed;inset:0;background:{background}">{overlay}</div>
<div style="position:fixed;inset:0;display:flex;flex-direction:column;align-items:{flex_align};
  justify-content:center;gap:4vh;padding:8vh 7vw;text-align:{align};color:{fg};font-family:{font};{shadow}">
  <div id="clock" style="font-size:5vh;opacity:.6;font-weight:300;letter-spacing:.3vw;font-variant-numeric:tabular-nums"></div>
  {f'<div style="font-size:{round(size * 0.55)}px;font-weight:600;opacity:.85;letter-spacing:.05em;{anim_use}">{title}</div>' if title else ''}
  <div style="font-size:{size}px;font-weight:{weight};line-height:1.2;max-width:86vw;{anim_use}animation-delay:.15s">{text}</div>
</div>
{f'<div style="position:fixed;right:1.4vw;bottom:1.2vh;font:1.5vh system-ui;color:#fff;opacity:.6;text-shadow:0 0 4px #000">{credit}</div>' if credit else ''}
{audio}
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
