"""
Alava Vision — Servidor (server.py) · versão 0.17.0

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
        http://localhost:8080/api/system/info?check=1 → versão instalada e se há atualização no GitHub (pede login)
        http://localhost:8080/api/player/alerts → avisos da TV (site no login, Waze fora) — pede login
        http://localhost:8080/api/traffic       → como o player abre o trânsito (Waze direto + faixa da Alava)
        http://localhost:8080/view/today?per=30 → "Hoje é dia" com 30 s por card
        http://localhost:8080/api/fx            → cotação do dólar do rodapé das notícias (comercial, 30 dias, PTAX)
        http://localhost:8080/api/news/<id_do_item_de_noticias>  → fila de notícias já ordenada (JSON; cada item
                                  traz source, category, preferred, weight). Ver "Notícias" no MAPA DO CÓDIGO.
    Testar os feeds do Portal Contábeis direto no terminal (sem abrir o painel):
        python -c "import server; r=server.get_news({'feeds':['https://www.contabeis.com.br/rss/conteudo/','https://www.contabeis.com.br/rss/noticias/','https://www.contabeis.com.br/rss/legislacao/']}, force=True); print(r['feeds']); print([(i['category'], i['title']) for i in r['items'][:8]])"
    Notícias (0.13.0) — onde ajustar (tudo em server.py, seção "Notícias (RSS / Atom)"):
        Tempo de cache ............... NEWS_TTL (padrão 600 s = 10 min; mude com NEWS_TTL=900 no .env)
        Pesos dos feeds .............. NEWS_DEFAULT_WEIGHTS (padrão do servidor) e config.weights (por item, no painel)
        Quem é "preferencial" ........ NEWS_PREFERRED_MIN (peso ≥ 8)
        Proporção preferenciais ...... NEWS_PREFERRED_RATIO (0.75 = 3 de cada 4); config.preferred_ratio por item
        Segundos de cada card ........ NEWS_SECONDS_PER_CARD (padrão 30; config.per_headline por item)
        Sem repetir (0.16.0) ......... NEWS_SEEN_DAYS (3 dias), data/news_seen.json, news_mark_seen(), get_news(tv=True)
        Revezamento entre fontes ..... _round_robin_by_source() (cada fonte entrega uma matéria por rodada)
        Palavras que sobem a matéria . NEWS_BOOST_WORDS (config.boost_words por item) e NEWS_BOOST_HOURS
        Idade máxima da notícia ...... NEWS_MAX_AGE_DAYS (config.max_age_days; 0 = sem limite)
        Indicadores (0.15.0) ......... _fx_fetch_ind(), _bcb_series(), BCB_SERIES (Selic, CDI, IPCA 12m, IGP-M, salário
                                       mínimo; cache FX_TTL_IND 6 h); Euro em _fx_fetch_live(); página B do rodapé
                                       (config.show_ind; alterna com o dólar a cada FX_PAGE_MS)
        Rodapé do dólar .............. get_fx() (FX_TTL_LIVE 2 min, FX_TTL_SLOW 30 min, FX_RETRY 1 min), _fx_fetch_live/
                                       _spark/_ptax (troque a fonte aqui), NEWS_FX_CSS/HTML/JS (visual; casas decimais: brl()),
                                       cache data/fx_cache.json; desliga por item com config.show_fx
        Cache no disco ............... data/news_cache.json (a TV continua com notícias se a internet cair e o servidor reiniciar)
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
    Para a 0.16.0 (antes da agenda fiscal, do aviso urgente e do relatório):
        git checkout a1bb3b8 -- server.py player.py static/index.html   (ou copie backup_v0.17.0_20261119/)
        As tabelas play_log e news_log ficam no banco e a 0.16.0 só as ignora.
    Para a 0.15.0 (antes da foto da TV, dos botões Voltar/Notícia e das notícias sem repetir):
        git checkout d2733ea -- server.py player.py static/index.html   (ou copie backup_v0.16.0_20261119/)
        O arquivo data/news_seen.json pode ser apagado (a 0.15.0 não usa).
    Para a 0.14.0 (antes dos avisos de login/Waze e dos indicadores no rodapé):
        git checkout d484a6f -- server.py player.py static/index.html   (ou copie backup_v0.14.0_20261119/)
        ferramentas/login_na_tv.bat é novo e pode ficar (nada depende dele).
    Para a 0.13.0 (antes do botão Atualizar, do trânsito no player e do tempo por card no "Hoje é dia"):
        git checkout 66da439 -- server.py player.py static/index.html atualizar.bat
        ou copie backup_v0.13.0_20261119/ (inclui o banco) por cima dos atuais.
    Para a 0.12.0 (antes da prioridade contábil nas notícias):
        git checkout main -- server.py static/index.html     (ou a tag backup-antes-rss-contabeis-20261119)
        ou copie backup_rss_20261119/server.py e backup_rss_20261119/static/ por cima dos atuais.
        Itens de notícias salvos na 0.13.0 abrem normalmente na 0.12.0 (os campos novos são ignorados).
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
    Atualizar pelo painel (0.14.0) .. GET /api/system/info, POST /api/system/update (roda atualizar.bat auto fora da
                                      árvore de processos do servidor), _git(), UPDATE_LOG/UPDATE_LOCK, _BOOT_ID
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
    Avisos da TV (0.15.0) ........... POST /api/player/alert (o player avisa, só localhost), GET /api/player/alerts,
                                      _player_alerts, ALERT_KINDS (login, waze); faixa no painel: #alerts-bar
    Na TV agora / pular item ........ POST /api/player/now (o player informa, só localhost), GET /api/player/now,
                                      POST /api/player/skip (_skip_seq → state["skip"] → WebSocket)
    Voltar item / notícia (0.16.0) .. POST /api/player/back (_back_seq → state["back"]), POST /api/player/card
                                      {dir: -1|1} (_card_cmd → state["card"]; o player chama newsNav() na tela)
    Foto da TV (0.16.0) ............. POST /api/player/shot (o player manda a cada 5 min, só localhost; fica na
                                      memória, _tv_shot), GET /api/player/shot (com login); hora em GET /api/player/now
    Agenda fiscal (0.17.0) .......... FISCAL_RULES (ONDE AJUSTAR UM PRAZO), _fiscal_date(), fiscal_upcoming(),
                                      _fiscal_custom(); GET /api/fiscal/rules, POST /api/fiscal-test, /view/fiscal/{id}
    Aviso urgente (0.17.0) .......... _urgent, urgent_active(), POST/DELETE /api/urgent, /view/urgent,
                                      state["urgent"] (assinatura do WebSocket); "Pular" com aviso no ar = encerrar
    Relatório da TV (0.17.0) ........ tabelas play_log e news_log; report_log_play() (dentro de POST /api/player/now),
                                      POST /api/player/skipped, report_data(), GET /api/report, GET /api/report.csv,
                                      report_prune() (REPORT_KEEP_DAYS = 90), END_REASONS
    Notícias sem repetir (0.16.0) ... /view/news/{id}?tv=1 e GET /api/news/{id}?tv=1; POST /api/news-seen (a tela da
                                      TV anota o card, só localhost), GET/DELETE /api/news-seen (painel: contar/zerar)
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
      tempo OBSERVADO (0.13.0) ...... _apply_observed() em get_weather(): condição, temperatura, umidade e sensação
                                      vêm do METAR do aeroporto mais próximo (_fetch_metar, _metar_code,
                                      _rh_from_dewpoint, _heat_index; METAR_STATION no .env). Sem METAR: modelo com
                                      a trava _sane_model_code(). current.*_model = o que o modelo dizia.
      comparação de modelos ......... _log_model_compare() → data/wx_compare.csv (WX_COMPARE no .env)
    Telas exibidas pelo player ...... /view/image/{id}, /view/video/{id}, /view/weather,
                                      /view/traffic (prévia; na TV o player abre o Waze direto: traffic_embed(),
                                      GET /api/traffic), /view/message/{id},
                                      /view/html/{id} (redireciona para /html/...), /view/countdown/{id}
      vídeo repetir ou não .......... view_video(): config.loop (padrão True)
      notícias (RSS) ................ /view/news/{id} (logo Alava no cabeçalho: config.show_logo, .top .logo), GET /api/news/{id}, POST /api/news-test,
                                      get_news() (filtro, sem repetidas), _fetch_feed() (cache NEWS_TTL),
                                      _parse_feed() (RSS e Atom), _warm_news() (em 2º plano, com o clima)
        itens antigos (0.14.0) ........ _migrate_news_sources() no startup(): ganham NEWS_MIGRATE_FEEDS uma vez
        prioridade contábil (0.13.0) . get_news() → _feed_weight() (peso por feed), _boost_hits() (palavras-chave),
                                      _news_dedupe_key() (mesma matéria em /conteudo e /noticias), _interleave()
                                      (fila ponderada: 3 de cada 4 vêm de feed preferencial); cada item sai com
                                      source/category/preferred/weight e r["feeds"] = contagem por feed ("Testar feed")
        cache em disco ................ _load_news_cache(), _save_news_cache() → data/news_cache.json
        selo na TV e foto padrão ...... view_news(): .tag (FONTE • CATEGORIA, .tag.pref = preferencial) e .pic.brand
                                      (logo Alava quando a matéria não traz foto)
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
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

__version__ = "0.17.0"

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
        # 0.17.0: relatório do que passou na TV (report_log_play) e das manchetes exibidas
        con.execute("""
            CREATE TABLE IF NOT EXISTS play_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT, started REAL, ended REAL,
                item_id TEXT, name TEXT, type TEXT, source TEXT, planned INTEGER, end_reason TEXT
            )""")
        con.execute("CREATE INDEX IF NOT EXISTS play_log_day ON play_log(day)")
        con.execute("""
            CREATE TABLE IF NOT EXISTS news_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT, at REAL, title TEXT, source TEXT,
                item_id TEXT, item_name TEXT
            )""")
        con.execute("CREATE INDEX IF NOT EXISTS news_log_day ON news_log(day)")
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


# ─── Atualizar o sistema pelo painel (0.14.0) ────────────────────────────────
#
# Configurações → Sistema → "Verificar atualização" / "Atualizar agora".
#   GET  /api/system/info?check=1 → versão, commit, se há versão nova no GitHub (git fetch) e o log da última
#                                   atualização (data/update.log).
#   POST /api/system/update       → roda atualizar.bat auto: fecha servidor/player/Chrome da TV, git pull, pip,
#                                   abre tudo de novo (iniciar_alava_vision.bat). O painel recarrega sozinho
#                                   quando o servidor volta (muda o "boot").
# Pegadinha: o atualizar.bat FECHA este servidor (taskkill /T, que mata a árvore de processos). Se o servidor
# abrisse o .bat como filho, o .bat morreria junto. Por isso ele é lançado por "cmd /c start …": o cmd
# intermediário termina na hora e o atualizador fica sem "pai", fora da árvore do servidor.
# Só funciona no Windows (onde a TV roda) e só para quem está logado no painel.
_BOOT_ID = f"{time.time():.0f}"            # muda a cada vez que o servidor sobe
UPDATE_LOG = DATA_DIR / "update.log"
UPDATE_LOCK = DATA_DIR / "update.lock"     # evita dois cliques seguidos; apagado quando o servidor volta
UPDATE_LOCK_MAX = 600                      # trava mais velha que 10 min é ignorada (atualização que falhou no meio)


def _git(*args: str, timeout: float = 25) -> tuple[int, str, str]:
    import subprocess
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")     # nunca fica esperando senha
    try:
        r = subprocess.run(["git", *args], cwd=str(BASE), capture_output=True, timeout=timeout, env=env,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except FileNotFoundError:
        return 127, "", "git não encontrado neste computador"
    except subprocess.TimeoutExpired:
        return 124, "", "o git demorou demais (sem internet?)"
    dec = lambda b: (b or b"").decode("utf-8", "replace").strip()
    return r.returncode, dec(r.stdout), dec(r.stderr)


def _update_running() -> bool:
    try:
        return time.time() - UPDATE_LOCK.stat().st_mtime < UPDATE_LOCK_MAX
    except OSError:
        return False


@app.get("/api/system/info", dependencies=[Depends(require_auth)])
def api_system_info(check: bool = False):
    info = {"version": __version__, "boot": _BOOT_ID, "updating": _update_running(), "windows": os.name == "nt"}
    rc, out, _ = _git("log", "-1", "--format=%h|%cd", "--date=format:%d/%m/%Y %H:%M")
    if rc == 0 and "|" in out:
        info["commit"], info["commit_date"] = out.split("|", 1)
    if check:
        rc, _, err = _git("fetch", "--quiet", timeout=45)
        if rc != 0:
            info["check_error"] = (err.splitlines() or ["falha no git fetch"])[-1][:200]
        else:
            rc, cnt, _ = _git("rev-list", "--count", "HEAD..@{u}")
            info["behind"] = int(cnt) if rc == 0 and cnt.isdigit() else 0
            _, log, _ = _git("log", "--oneline", "--no-merges", "-15", "HEAD..@{u}")
            info["news"] = [l for l in log.splitlines() if l.strip()]
        _, dirty, _ = _git("status", "--porcelain", "--untracked-files=no")
        info["dirty"] = [l for l in dirty.splitlines() if l.strip()][:10]   # arquivos mexidos à mão: o pull pode falhar
    try:
        lines = UPDATE_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        info["last_update"] = {"at": datetime.fromtimestamp(UPDATE_LOG.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
                               "log": [l for l in lines if l.strip()][-30:]}
    except OSError:
        pass
    return info


@app.post("/api/system/update", dependencies=[Depends(require_auth)])
def api_system_update():
    import subprocess
    if os.name != "nt":
        raise HTTPException(501, "A atualização pelo painel só funciona no Windows (computador da TV).")
    bat = BASE / "atualizar.bat"
    if not bat.exists():
        raise HTTPException(404, "atualizar.bat não encontrado na pasta do sistema.")
    if _update_running():
        raise HTTPException(409, "Já existe uma atualização em andamento.")
    UPDATE_LOCK.write_text(datetime.now().isoformat(), encoding="utf-8")
    # start "título" /min cmd /c ""<bat>" auto > "<log>" 2>&1"  — janela minimizada, saída no data\update.log
    inner = f'""{bat}" auto > "{UPDATE_LOG}" 2>&1"'
    subprocess.Popen(f'cmd /c start "Alava Vision - Atualizar" /min cmd /c {inner}', cwd=str(BASE),
                     creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS, close_fds=True)
    print("[sistema] atualização pedida pelo painel — o servidor vai reiniciar")
    return {"ok": True, "boot": _BOOT_ID}


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
    state["back"] = _back_seq   # 0.16.0: botão "Voltar item"
    state["card"] = [_card_cmd["seq"], _card_cmd["dir"]]   # 0.16.0: notícia anterior/próxima ([nº do clique, -1|1])
    u = urgent_active()                   # 0.17.0: aviso urgente por cima da programação
    state["urgent"] = {"id": u["id"], "until": u["until"]} if u else None
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
    await asyncio.to_thread(report_log_play, body)     # 0.17.0: relatório do que passou na TV
    return {"ok": True}


@app.get("/api/player/now")
def player_now():
    """O que o player disse que está na tela e há quantos segundos ("stale" se faz tempo demais).
    shot_ts/shot_at/shot_item (0.16.0): quando chegou a última foto da TV e de qual item."""
    shot = ({"shot_ts": _tv_shot["at"], "shot_at": datetime.fromtimestamp(_tv_shot["at"]).strftime("%H:%M"),
             "shot_item": _tv_shot["item"]} if _tv_shot else {"shot_ts": 0})
    if not _now_playing:
        return {"playing": False, **shot, **urgent_public()}
    elapsed = time.time() - _now_playing["started"]
    dur = int(_now_playing.get("duration") or 0)
    return {"playing": True, **_now_playing, "elapsed": round(elapsed, 1),
            "remaining": max(0, round(dur - elapsed)),
            # passou bem do tempo e o player não avisou o item seguinte: provavelmente está fechado
            "stale": elapsed > dur + 90, "players": len(_players), **shot, **urgent_public()}


# ─── Avisos do player para o painel (0.15.0) ─────────────────────────────────
#
# O player conta ao servidor quando um item não pode ir ao ar e ele está PULANDO esse item:
#   kind "login" → um site (ex.: Acessórias) abriu na tela de login/captcha (sessão expirou);
#   kind "waze"  → o Waze não abriu ou não entregou os dados de trânsito.
# O painel mostra uma faixa de aviso em todas as abas (GET /api/player/alerts, a cada 30 s) com o
# que fazer. O player limpa o aviso sozinho quando o item volta a funcionar (active=false).
# Fica só na memória: se o servidor reiniciar, o player avisa de novo na próxima tentativa.
_player_alerts: dict[str, dict] = {}
ALERT_KINDS = {"login", "waze"}


@app.post("/api/player/alert")
async def player_alert_report(request: Request):
    if not request.client or request.client.host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(403, "Só o player deste computador envia avisos")
    b = await request.json()
    key, kind = str(b.get("key") or "")[:120], b.get("kind")
    if not key or kind not in ALERT_KINDS:
        raise HTTPException(400, "Aviso inválido")
    if not b.get("active"):
        if _player_alerts.pop(key, None):
            print(f"[aviso] resolvido: {key}")
        return {"ok": True}
    now = time.time()
    old = _player_alerts.get(key)
    _player_alerts[key] = {"key": key, "kind": kind, "item_id": b.get("item_id"), "item_name": str(b.get("item_name") or "")[:120],
                           "url": str(b.get("url") or "")[:300], "detail": str(b.get("detail") or "")[:300],
                           "since": old["since"] if old else now, "last": now}
    if not old:
        print(f"[aviso] {kind}: {_player_alerts[key]['item_name']} — {_player_alerts[key]['detail']}")
    return {"ok": True}


@app.get("/api/player/alerts", dependencies=[Depends(require_auth)])
def player_alerts():
    fmt = lambda t: datetime.fromtimestamp(t).strftime("%d/%m %H:%M")
    return {"dir": str(BASE), "alerts": [dict(a, since_txt=fmt(a["since"]), last_txt=fmt(a["last"]))
                                         for a in sorted(_player_alerts.values(), key=lambda a: a["since"])]}


@app.post("/api/player/skip", dependencies=[Depends(require_auth)])
def player_skip():
    global _skip_seq
    if urgent_active():          # 0.17.0: "Pular" com aviso urgente no ar = encerrar o aviso
        _urgent.clear()
        return {"ok": True, "urgent_closed": True, "players": len(_players)}
    _skip_seq += 1
    return {"ok": True, "skip": _skip_seq, "players": len(_players)}


# ─── Voltar item / notícia anterior e próxima (0.16.0) ───────────────────────
# Mesmo caminho do "Pular item": um contador vai no estado e na assinatura do WebSocket.
#   "back" → o player encerra o item e mostra o ANTERIOR da fila;
#   "card" → [nº do clique, -1|1]: se a TV está nas notícias, o player chama newsNav() na página
#            (o item continua no ar; só troca a manchete).
_back_seq = 0
_card_cmd = {"seq": 0, "dir": 0}


@app.post("/api/player/back", dependencies=[Depends(require_auth)])
def player_back():
    global _back_seq
    _back_seq += 1
    return {"ok": True, "back": _back_seq, "players": len(_players)}


@app.post("/api/player/card", dependencies=[Depends(require_auth)])
async def player_card(request: Request):
    body = await request.json()
    d = -1 if int(body.get("dir") or 1) < 0 else 1
    _card_cmd.update(seq=_card_cmd["seq"] + 1, dir=d)
    return {"ok": True, "dir": d, "players": len(_players)}


# ─── Foto da TV no painel (0.16.0) ──────────────────────────────────────────
# O player tira uma foto pequena da tela a cada 5 min (PLAYER SHOT_EVERY) e manda aqui
# (POST /api/player/shot, só do próprio computador). Fica SÓ NA MEMÓRIA: reiniciar o servidor apaga.
# O painel mostra ao lado de "Na TV agora" com "Última atualização em HH:MM" (GET /api/player/shot,
# exige login: a tela do Acessórias mostra dados de clientes).
_tv_shot: dict = {}
SHOT_MAX_BYTES = 3_000_000


@app.post("/api/player/shot")
async def player_shot_upload(request: Request, item: str = ""):
    if not _is_local(request):
        raise HTTPException(403, "Só o player deste computador manda a foto da TV")
    data = await request.body()
    if not data or len(data) > SHOT_MAX_BYTES or not data.startswith(b"\xff\xd8"):
        raise HTTPException(400, "Foto inválida (esperado JPEG de até 3 MB)")
    _tv_shot.update(jpg=data, at=time.time(), item=item[:120])
    return {"ok": True}


@app.get("/api/player/shot", dependencies=[Depends(require_auth)])
def player_shot():
    if not _tv_shot:
        raise HTTPException(404, "O player ainda não mandou nenhuma foto")
    return Response(_tv_shot["jpg"], media_type="image/jpeg", headers={"Cache-Control": "no-store"})


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
            tuple(state.get("notices") or ()), state.get("skip"), state.get("back"),
            tuple(state.get("card") or ()), (state.get("urgent") or {}).get("id"))


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
    # /api/player/now, a foto da TV e a anotação de notícias exibidas vêm do próprio player: não mudam a programação
    if (request.method in ("POST", "PUT", "DELETE") and request.url.path.startswith("/api/")
            and request.url.path not in ("/api/player/now", "/api/player/shot", "/api/news-seen", "/api/player/skipped",
                                         "/api/fiscal-test", "/api/news-test")
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
#
# PRIORIDADE CONTÁBIL (0.13.0). Cada feed tem um PESO de 1 a 10 (config.weights[url]; sem ele vale
# NEWS_DEFAULT_WEIGHTS; sem nenhum, 5). Feeds com peso ≥ NEWS_PREFERRED_MIN são "preferenciais".
# Quando o item tem pelo menos um feed preferencial, get_news() troca a ordenação só-por-data por:
#   1. descarta matéria velha demais (NEWS_MAX_AGE_DAYS) — o /rss/legislacao/ do Contábeis está
#      parado em 2020 e não pode aparecer na TV como se fosse novidade;
#   2. tira repetidas (mesmo link ou mesmo título — /rss/conteudo/ e /rss/noticias/ repetem ~70%),
#      ficando com a cópia do feed de maior peso;
#   3. dá nota a cada matéria = recência + bônus do peso + bônus por palavra-chave no título;
#   4. entrega em fila ponderada: NEWS_PREFERRED_RATIO das vagas para preferenciais (0.75 = 3 de
#      cada 4) e o resto para as demais fontes; se um grupo acabar, o outro completa a fila.
# Item sem feed preferencial continua exatamente como antes (só por data).

NEWS_TTL = int(os.getenv("NEWS_TTL", "600"))             # cache de cada feed, em segundos (10 min)
NEWS_FETCH_TIMEOUT = 10                                  # espera máxima por feed, em segundos
NEWS_USER_AGENT = "Mozilla/5.0 (compatible; AlavaVision/0.13; leitor de RSS)"
NEWS_CACHE_FILE = DATA_DIR / "news_cache.json"          # cópia em disco: sobrevive a reinício sem internet
_news_cache: dict[str, tuple[float, list[dict]]] = {}   # url → (quando, manchetes)
_news_cache_lock = threading.Lock()
_news_cache_loaded = False
# Nome exibido da fonte quando o título do canal não ajuda (ex.: Agência Brasil manda "Feed Últimas")
NEWS_SOURCE_NAMES = {"agenciabrasil.ebc.com.br": "Agência Brasil", "feeds.bbci.co.uk": "BBC News Brasil",
                     "www.infomoney.com.br": "InfoMoney", "www.contabeis.com.br": "Portal Contábeis",
                     "www.jornalcontabil.com.br": "Jornal Contábil", "www.cfc.org.br": "CFC",
                     "www.fenacon.org.br": "FENACON", "www.conjur.com.br": "ConJur"}
# Categoria da etiqueta quando a matéria não traz <category> (o /rss/legislacao/ não traz).
# Chave = trecho do endereço do feed.
NEWS_FEED_CATEGORIES = {"contabeis.com.br/rss/legislacao": "Legislação", "contabeis.com.br/rss/noticias": "Notícias",
                        "contabeis.com.br/rss/conteudo": "Conteúdo"}
# ── ONDE AJUSTAR OS PESOS ── (1 = mínimo, 10 = máximo). O painel grava o peso de cada feed no item
# (Alta = 10, Normal = 5, Baixa = 2); esta tabela vale para itens que ainda não têm peso salvo.
NEWS_DEFAULT_WEIGHTS = {
    "https://www.contabeis.com.br/rss/conteudo/": 10,     # Portal Contábeis — últimas matérias (principal)
    "https://www.contabeis.com.br/rss/noticias/": 9,      # Portal Contábeis — notícias publicadas
    "https://www.contabeis.com.br/rss/legislacao/": 10,   # Portal Contábeis — atos legais (máxima)
    "https://www.contabeis.com.br/rss/artigos/": 8,       # Portal Contábeis — artigos
    "https://www.jornalcontabil.com.br/feed/": 9,         # Jornal Contábil — notícias para contadores
    "https://www.cfc.org.br/feed/": 9,                    # CFC — Conselho Federal de Contabilidade (oficial)
    "https://www.fenacon.org.br/feed/": 8,                # FENACON — federação das empresas contábeis
}                                                         # (ConJur Tributário e Agência Brasil Economia ficam no peso normal)
NEWS_DEFAULT_WEIGHT = 5          # feed sem peso definido
NEWS_PREFERRED_MIN = 8           # peso a partir do qual o feed é "Preferencial / Foco Contábil"
NEWS_PREFERRED_RATIO = 0.75      # fatia da fila para preferenciais (0.75 = 3 de cada 4 notícias)
NEWS_MAX_AGE_DAYS = 30           # no modo prioridade, ignora matéria mais velha que isto (0 = sem limite)
# ── ONDE AJUSTAR AS PALAVRAS-CHAVE ── (separadas por vírgula; sem diferenciar acento/maiúscula; cada
# palavra vale como INÍCIO de palavra: "fiscal" pega "fiscalização"). Só olha o TÍTULO.
NEWS_BOOST_WORDS = ("receita federal, simples nacional, irpf, imposto de renda, dctfweb, esocial, reforma tributária, "
                    "icms, iss, pis, cofins, sped, nota fiscal, fiscal, prazo, legislação, mei, tributári, "
                    "folha de pagamento, inss, fgts, cnd, ecf, ecd")
NEWS_SECONDS_PER_CARD = 30       # tempo padrão de cada card de notícia na TV (config.per_headline; era 9 s até a 0.12.0)
NEWS_BOOST_HOURS = 8            # cada palavra-chave "rejuvenesce" a matéria em 8 h na fila (máx. 3 palavras)
NEWS_WEIGHT_HOURS = 2            # cada ponto de peso acima de 5 vale 2 h de vantagem (peso 10 = +10 h)

# ── NOTÍCIAS SEM REPETIR (0.16.0) ──
# Antes, cada vez que o item de notícias entrava, a TV mostrava as mesmas max_items manchetes (15 cards
# de 20 s num item de 300 s = a lista inteira, ~15 vezes por dia). Agora o player abre a tela com ?tv=1,
# e cada card que fica na tela é anotado em data/news_seen.json ("t:<título>" e "l:<link>" → hora).
# O registro é UM SÓ para todos os itens de notícias: a Manhã não repete o que a Tarde já mostrou.
# Na montagem do pacote (get_news com tv=True): primeiro as NUNCA exibidas (na ordem de prioridade de
# sempre); quando acabam, as exibidas HÁ MAIS TEMPO. Anotações com mais de NEWS_SEEN_DAYS dias somem.
# A prévia do painel e o "Testar feed" não anotam nada (não têm ?tv=1).
# Zerar: Painel → item de notícias → "Zerar histórico" (DELETE /api/news-seen) ou apague o arquivo.
NEWS_SEEN_FILE = DATA_DIR / "news_seen.json"
NEWS_SEEN_DAYS = 3
_news_seen: dict[str, float] | None = None      # carregado do disco no 1º uso
_news_seen_lock = threading.Lock()


def _news_seen_data() -> dict[str, float]:
    """O registro (já sem as anotações vencidas). Chamar com _news_seen_lock."""
    global _news_seen
    if _news_seen is None:
        try:
            _news_seen = {str(k): float(v) for k, v in json.loads(NEWS_SEEN_FILE.read_text(encoding="utf-8")).items()}
        except (OSError, ValueError, TypeError, AttributeError):
            _news_seen = {}          # 1ª vez ou arquivo corrompido
    limit = time.time() - NEWS_SEEN_DAYS * 86400
    for k in [k for k, t in _news_seen.items() if t < limit]:
        del _news_seen[k]
    return _news_seen


def _news_seen_save() -> None:
    """Grava o registro (chamar com _news_seen_lock). Arquivo temporário + troca: nunca fica pela metade."""
    try:
        tmp = NEWS_SEEN_FILE.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(_news_seen or {}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(NEWS_SEEN_FILE)
    except OSError as e:
        print(f"[notícias] não consegui gravar o histórico de exibidas: {e}")


def news_mark_seen(title: str, link: str = "") -> None:
    link_key, title_key = _news_dedupe_keys({"title": title, "link": link})
    if not title_key and not link_key:
        return
    with _news_seen_lock:
        seen, now = _news_seen_data(), time.time()
        if title_key:
            seen["t:" + title_key] = now
        if link_key:
            seen["l:" + link_key] = now
        _news_seen_save()


def news_seen_snapshot() -> dict[str, float]:
    with _news_seen_lock:
        return dict(_news_seen_data())


def _local(tag: str) -> str:
    """'{http://search.yahoo.com/mrss/}content' → 'content'."""
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _strip_html(s: str) -> str:
    import re
    s = re.sub(r"<[^>]+>", " ", s or "")
    return " ".join(html.unescape(s).split())


def _clean_summary(s: str) -> str:
    """Tira do resumo o rodapé "Leia mais em https://…" (o Contábeis manda em toda matéria) e
    endereços soltos: na TV ninguém clica, e a linha só ocupa espaço."""
    import re
    s = re.sub(r"\s*(?:leia mais|veja mais|saiba mais|continue lendo)[^.]{0,12}\s*https?://\S+", "", s, flags=re.I)
    s = re.sub(r"https?://\S+", "", s)
    # WordPress (Jornal Contábil, CFC, FENACON, ConJur) fecha o resumo com "O post X apareceu primeiro em Y."
    # e usa "[…]" para cortar o texto.
    s = re.sub(r"\s*(?:O post|The post)\b.{0,300}?(?:apareceu primeiro (?:em|no|na)|appeared first on)\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s*\[(?:…|\.\.\.)\]\s*", "… ", s).strip()
    return " ".join(s.split())


def _first_image(markup: str) -> str:
    """Primeira foto de verdade dentro de um trecho de HTML (o <content:encoded> dos feeds WordPress).
    Pula emoji, avatar, pixel de rastreio e imagens minúsculas, que viram "foto" de uma notícia à toa."""
    import re
    for tag in re.finditer(r"<img\b[^>]*>", html.unescape(markup or ""), flags=re.I):
        t = tag.group(0)
        m = re.search(r"""\bsrc=["']([^"']+)""", t, flags=re.I)
        if not m or not m.group(1).startswith(("http://", "https://")):
            continue
        src = m.group(1)
        if re.search(r"emoji|gravatar|smilies|pixel|spacer|1x1|/avatar", src, flags=re.I):
            continue
        size = re.findall(r"""\b(?:width|height)=["']?(\d+)""", t, flags=re.I)
        if size and min(int(x) for x in size) < 80:
            continue
        return src
    return ""


def _plain(s: str) -> str:
    """Minúsculas e sem acento/pontuação — para comparar títulos e palavras-chave."""
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


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
        f = {"title": "", "summary": "", "image": "", "ts": 0.0, "link": "", "category": ""}
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
            elif name == "encoded" and not f["image"]:
                f["image"] = _first_image(text)        # <content:encoded> (WordPress): a foto vem aqui
            elif name == "category" and not f["category"]:
                # RSS: <category>Tributário</category>; Atom: <category term="Tributário"/>
                f["category"] = _strip_html(text or ch.get("term", ""))[:40]
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
        f["summary"] = _clean_summary(f["summary"])
        if len(f["summary"]) > 240:
            f["summary"] = f["summary"][:237].rsplit(" ", 1)[0] + "…"
        if f["title"]:
            host = urllib.parse.urlparse(url).hostname or ""
            f["source"] = NEWS_SOURCE_NAMES.get(host) or source or host
            if not f["category"]:        # feed sem <category> (ex.: legislação): usa o nome da seção
                f["category"] = next((c for k, c in NEWS_FEED_CATEGORIES.items() if k in url.lower()), "")
            if f["category"] and _plain(f["category"]) in _plain(f["source"]):
                f["category"] = ""       # g1 manda <category>G1</category> e a fonte já é "g1 > Economia": selo repetido
            out.append(f)
    return out


def _load_news_cache() -> None:
    """Lê data/news_cache.json uma vez, no 1º uso. É o "último cache válido": se a internet cair
    com o servidor desligado, a TV volta com as notícias de antes em vez de ficar vazia."""
    global _news_cache_loaded
    if _news_cache_loaded:
        return
    _news_cache_loaded = True
    try:
        saved = json.loads(NEWS_CACHE_FILE.read_text(encoding="utf-8"))
        for url, (when, items) in saved.items():
            _news_cache.setdefault(url, (float(when), items))
    except (OSError, ValueError, TypeError):
        pass   # sem arquivo (1ª vez) ou arquivo corrompido: começa vazio


def _save_news_cache() -> None:
    try:
        with _news_cache_lock:
            snapshot = {u: [w, it] for u, (w, it) in _news_cache.items()}
            tmp = NEWS_CACHE_FILE.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")   # nome único: 2 servidores na mesma pasta não se atropelam
            tmp.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
            tmp.replace(NEWS_CACHE_FILE)          # troca atômica: nunca fica pela metade
    except OSError as e:
        print(f"[notícias] não consegui gravar o cache em disco: {e}")


def _fetch_feed(url: str, force: bool = False) -> list[dict]:
    _load_news_cache()
    hit = _news_cache.get(url)
    if hit and not force and time.time() - hit[0] < NEWS_TTL:
        return hit[1]
    import gzip
    req = urllib.request.Request(url, headers={"User-Agent": NEWS_USER_AGENT, "Accept-Encoding": "identity",
                                               "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    try:
        with urllib.request.urlopen(req, timeout=NEWS_FETCH_TIMEOUT) as r:
            data = r.read(5 * 1024 * 1024)
        if data[:2] == b"\x1f\x8b":          # alguns servidores mandam gzip mesmo sem pedir
            data = gzip.decompress(data)
        items = _parse_feed(data.lstrip(b"\xef\xbb\xbf \t\r\n"), url)
    except Exception:
        if hit:                  # sem internet: usa o que tinha (memória ou disco)
            return hit[1]
        raise
    _news_cache[url] = (time.time(), items)
    _save_news_cache()
    return items


def _feed_weight(url: str, cfg: dict) -> int:
    """Peso 1–10 do feed: o do item (config.weights) → o padrão do servidor → NEWS_DEFAULT_WEIGHT."""
    saved = cfg.get("weights")
    w = saved.get(url) if isinstance(saved, dict) else None
    if w is None:
        w = NEWS_DEFAULT_WEIGHTS.get(url)
    if w is None:   # mesmo feed escrito sem a "/" final
        w = NEWS_DEFAULT_WEIGHTS.get(url.rstrip("/") + "/")
    return _num(w, NEWS_DEFAULT_WEIGHT, 1, 10)


def _boost_hits(title: str, boost_re) -> int:
    """Quantas palavras-chave estratégicas aparecem no título (no máximo 3)."""
    if not boost_re:
        return 0
    return min(3, len({m.group(0) for m in boost_re.finditer(_plain(title))}))


def _news_dedupe_keys(it: dict) -> tuple[str, str]:
    """(link, título) normalizados: a mesma matéria vinda de feeds diferentes tem um dos dois igual."""
    link = (it.get("link") or "").split("#")[0].split("?")[0].rstrip("/").lower()
    return link, _plain(it.get("title"))


def _round_robin_by_source(items: list[dict]) -> list[dict]:
    """Reveza as fontes dentro de um grupo (recebe a lista já ordenada pela nota). Sem isto, uma fonte que
    publica toda hora (o Contábeis, a cada 30 min) ocuparia todas as vagas e as outras nunca apareceriam.
    Cada fonte entrega a sua melhor matéria por vez; a fonte com a melhor nota abre a rodada."""
    groups: dict[str, list[dict]] = {}
    for it in items:
        groups.setdefault(it["source"], []).append(it)
    rounds = sorted(groups.values(), key=lambda g: -g[0]["score"])
    out = []
    while any(rounds):
        for g in rounds:
            if g:
                out.append(g.pop(0))
    return out


def _interleave(pref: list[dict], other: list[dict], ratio: float, limit: int) -> list[dict]:
    """Fila ponderada: de cada vaga, `ratio` vai para os preferenciais (0.75 → P P G P, P P G P…).
    Se um dos grupos acabar, o outro completa até `limit`. Cada lista já vem ordenada pela nota."""
    out, taken_pref = [], 0
    pref, other = list(pref), list(other)
    while len(out) < limit and (pref or other):
        # Quantos preferenciais já deveriam ter saído depois desta vaga?
        want_pref = int(ratio * (len(out) + 1) + 0.5) > taken_pref
        if (want_pref and pref) or not other:
            out.append(pref.pop(0))
            taken_pref += 1
        else:
            out.append(other.pop(0))
    return out


def get_news(cfg: dict, force: bool = False, tv: bool = False) -> dict:
    """Fila de manchetes do item. tv=True (0.16.0): a TV pediu — as já exibidas (news_seen) vão para o fim."""
    import re
    from concurrent.futures import ThreadPoolExecutor
    feeds = [u.strip() for u in cfg.get("feeds", []) if str(u).strip().startswith(("http://", "https://"))][:12]
    # Cada palavra vale como INÍCIO de palavra: "assassin" pega "assassinato", mas
    # "morta" não pega "imortal" nem "comporta".
    words = [w.strip().lower() for w in str(cfg.get("block_words", "")).split(",") if w.strip()]
    block_re = re.compile(r"\b(" + "|".join(map(re.escape, words)) + ")") if words else None
    max_items = _num(cfg.get("max_items"), 15, 1, 60)

    # Prioridade contábil: só liga se houver pelo menos um feed preferencial (peso alto) no item.
    weights = {u: _feed_weight(u, cfg) for u in feeds}
    prio = cfg.get("prioritize", True) and any(w >= NEWS_PREFERRED_MIN for w in weights.values())
    ratio = max(0.0, min(1.0, _num(cfg.get("preferred_ratio"), int(NEWS_PREFERRED_RATIO * 100), 0, 100) / 100))
    max_age = _num(cfg.get("max_age_days"), NEWS_MAX_AGE_DAYS if prio else 0, 0, 3650)
    boost_src = cfg["boost_words"] if "boost_words" in cfg else NEWS_BOOST_WORDS
    boost_words = [_plain(w) for w in str(boost_src).split(",") if _plain(w)]
    boost_re = re.compile(r"\b(" + "|".join(map(re.escape, boost_words)) + ")") if boost_words and prio else None

    items, errors, stats = [], [], []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for url, res in zip(feeds, ex.map(lambda u: _try(_fetch_feed, u, force), feeds)):
            host = urllib.parse.urlparse(url).hostname
            if isinstance(res, Exception):
                errors.append(f"{host}: {res}")
                stats.append({"url": url, "weight": weights[url], "read": 0, "fresh": 0, "error": str(res)[:120]})
            else:
                # cópia: o cache guarda os dicionários originais e aqui eles ganham campos de trabalho
                items += [dict(i, feed=url, weight=weights[url]) for i in res]
                stats.append({"url": url, "weight": weights[url], "read": len(res), "fresh": 0, "error": ""})
    # "VÍDEOS: Jornal da Manhã…" e "EPTV 1 Campinas ao vivo" (g1) são listas de vídeos e
    # chamadas de transmissão: na TV viram um título sem conteúdo, então saem.
    # "VÍDEO: cratera engole caminhão" (singular) é notícia de verdade: só perde o prefixo.
    video_re = re.compile(r"^v[íi]deos\s*:|\bao vivo\s*$", re.I) if cfg.get("skip_videos", True) else None
    for it in items:
        it["title"] = re.sub(r"^v[íi]deo\s*:\s*", "", it["title"], flags=re.I)

    now = time.time()
    for it in items:
        # nota (em "horas de frescor"): quanto maior, mais cedo na fila
        it["score"] = it["ts"] / 3600.0
        if prio:
            it["score"] += (it["weight"] - 5) * NEWS_WEIGHT_HOURS + _boost_hits(it["title"], boost_re) * NEWS_BOOST_HOURS
    # Cópia de feed de maior peso vem primeiro (e vence a deduplicação); depois, a mais pontuada.
    items.sort(key=lambda x: (-x["weight"] if prio else 0, -x["score"]))

    seen_link, seen_title, kept = set(), set(), []
    fresh = {}
    for it in items:
        text = (it["title"] + " " + it["summary"]).lower()
        if (block_re and block_re.search(text)) or (video_re and video_re.search(it["title"])):
            continue
        if max_age and it["ts"] and now - it["ts"] > max_age * 86400:
            continue                                               # velha demais (ex.: legislação de 2020)
        fresh[it["feed"]] = fresh.get(it["feed"], 0) + 1           # conta ANTES de deduplicar ("Testar feed")
        link, title = _news_dedupe_keys(it)
        if (link and link in seen_link) or title in seen_title:
            continue                                               # a mesma matéria já entrou por outro feed
        if link:
            seen_link.add(link)
        seen_title.add(title)
        kept.append(it)
    for s in stats:
        s["fresh"] = fresh.get(s["url"], 0)

    # Notícias sem repetir (0.16.0): na TV, separa as já exibidas. As novas seguem a ordem de sempre;
    # as exibidas só completam o pacote quando as novas acabam, da exibida há mais tempo para a mais recente.
    seen = news_seen_snapshot() if tv else {}

    def last_seen(it: dict) -> float:
        link, title = _news_dedupe_keys(it)
        return max(seen.get("t:" + title, 0.0), seen.get("l:" + link, 0.0) if link else 0.0)
    new_items = [i for i in kept if not last_seen(i)] if seen else kept
    old_items = sorted((i for i in kept if last_seen(i)), key=last_seen) if seen else []

    if prio:
        pref = _round_robin_by_source(sorted((i for i in new_items if i["weight"] >= NEWS_PREFERRED_MIN), key=lambda x: -x["score"]))
        other = _round_robin_by_source(sorted((i for i in new_items if i["weight"] < NEWS_PREFERRED_MIN), key=lambda x: -x["score"]))
        ordered = _interleave(pref, other, ratio, max_items)
    else:
        ordered = sorted(new_items, key=lambda x: -x["ts"])[:max_items]    # como na 0.12.0: só por data
    ordered += old_items[:max_items - len(ordered)]
    out = []
    for it in ordered:
        it["preferred"] = prio and it["weight"] >= NEWS_PREFERRED_MIN
        for k in ("feed", "score"):
            it.pop(k, None)
        out.append(it)
    return {"items": out, "errors": errors, "feeds": stats, "priority": bool(prio),
            "updated_at": datetime.now().strftime("%H:%M"),
            "unseen": len(new_items), "seen": len(old_items)}     # 0.16.0: sobram N novas (só com tv=True)


def _try(fn, *a):
    try:
        return fn(*a)
    except Exception as e:
        return e


# Fontes contábeis que os itens de notícias ANTIGOS ganham (0.14.0, pedido de 19/11/2026).
NEWS_MIGRATE_FEEDS = ("https://www.contabeis.com.br/rss/conteudo/", "https://www.contabeis.com.br/rss/noticias/",
                      "https://www.contabeis.com.br/rss/legislacao/", "https://www.jornalcontabil.com.br/feed/",
                      "https://www.cfc.org.br/feed/", "https://www.fenacon.org.br/feed/")


def _migrate_news_sources() -> int:
    """Roda a cada início do servidor, mas só age uma vez por item: itens de notícias salvos ANTES da 0.13.0
    (sem config.weights) ganham as fontes contábeis acima, mantendo as que já tinham (que viram as fontes
    "gerais" da fila 3:1). Grava os pesos, então na próxima vez o item é reconhecido como já migrado.
    Item salvo pelo painel na 0.13.0+ já tem pesos: as fontes escolhidas ali não são tocadas.
    Tempo por card e quantidade de cards não mudam (o item continua com o tempo que tinha)."""
    n = 0
    try:
        with db() as con:
            for r in con.execute("SELECT id, name, config FROM items WHERE type='news'").fetchall():
                cfg = json.loads(r["config"] or "{}")
                if isinstance(cfg.get("weights"), dict):
                    continue
                feeds = [u for u in (cfg.get("feeds") or []) if isinstance(u, str)]
                feeds += [u for u in NEWS_MIGRATE_FEEDS if u not in feeds]
                cfg["feeds"] = feeds[:12]                       # get_news() lê no máximo 12
                cfg["weights"] = {u: _feed_weight(u, cfg) for u in cfg["feeds"]}
                con.execute("UPDATE items SET config=? WHERE id=?", (json.dumps(cfg, ensure_ascii=False), r["id"]))
                n += 1
                print(f"[notícias] item antigo '{r['name']}' ganhou as fontes contábeis ({len(cfg['feeds'])} fontes)")
    except Exception as e:
        print(f"[notícias] não consegui atualizar os itens antigos: {e}")
    return n


@app.get("/api/news/{item_id}")
def api_news(item_id: str, tv: int = 0):
    return get_news(_item_config(item_id), tv=bool(tv))


def _is_local(request: Request) -> bool:
    return bool(request.client) and request.client.host in ("127.0.0.1", "::1", "localhost")


@app.post("/api/news-seen")
async def news_seen_add(request: Request):
    """A tela de notícias da TV (aberta com ?tv=1) anota o card que ficou na tela. Só do próprio computador."""
    if not _is_local(request):
        raise HTTPException(403, "Só a TV deste computador anota as notícias exibidas")
    body = await request.json()
    news_mark_seen(str(body.get("title") or ""), str(body.get("link") or ""))
    try:                                   # 0.17.0: relatório das manchetes exibidas
        with db() as con:
            con.execute("INSERT INTO news_log (day, at, title, source, item_id, item_name) VALUES (?,?,?,?,?,?)",
                        (datetime.now().strftime("%Y-%m-%d"), time.time(), str(body.get("title") or "")[:300],
                         str(body.get("source") or "")[:80], str(body.get("item_id") or "")[:20],
                         str(body.get("item_name") or "")[:120]))
            con.commit()
    except sqlite3.Error as e:
        print(f"[relatório] {e}")
    return {"ok": True}


@app.get("/api/news-seen", dependencies=[Depends(require_auth)])
def news_seen_info():
    seen = news_seen_snapshot()
    return {"count": sum(1 for k in seen if k.startswith("t:")), "days": NEWS_SEEN_DAYS}


@app.delete("/api/news-seen", dependencies=[Depends(require_auth)])
def news_seen_clear():
    global _news_seen
    with _news_seen_lock:
        _news_seen = {}
        _news_seen_save()
    return {"ok": True}


@app.post("/api/news-test", dependencies=[Depends(require_auth)])
async def api_news_test(request: Request):
    """Painel: testa os feeds digitados antes de salvar (mostra quantas manchetes e os erros)."""
    return await asyncio.to_thread(get_news, await request.json(), True)


# ─── Cotação do dólar (rodapé da tela de notícias, 0.13.0) ───────────────────
#
# Três dados, cada um com seu cache (memória + data/fx_cache.json):
#   • "live"  — dólar comercial agora: AwesomeAPI /json/last/USD-BRL (grátis, sem chave; muda a cada ~1 min).
#               Traz compra (bid), variação do dia (%), mínima e máxima.            → FX_TTL_LIVE (2 min)
#   • "spark" — fechamento dos últimos 30 dias: AwesomeAPI /json/daily/USD-BRL/30.  → FX_TTL_SLOW (30 min)
#               O último ponto (hoje) é trocado pelo valor ao vivo, então a linha se mexe durante o dia.
#               (A série "intradiária" da API vem limitada a 100 pontos e, no teste, às vezes devolveu
#               dados de dias atrás: por isso o gráfico é de 30 dias.)
#   • "ptax"  — PTAX de venda do Banco Central (taxa oficial usada na contabilidade). → FX_TTL_SLOW
#               Sai por volta das 13h; antes disso vale a do dia útil anterior.
# Sem internet: usa o último valor salvo e espera FX_RETRY s antes de tentar de novo (a tela não trava).
# Para trocar a fonte, mexa só em _fx_fetch_*; o formato entregue por get_fx() é o que a tela usa.

FX_TTL_LIVE = 120
FX_TTL_SLOW = 1800
FX_RETRY = 60
FX_TIMEOUT = 6
FX_CACHE_FILE = DATA_DIR / "fx_cache.json"
_fx: dict[str, dict] = {}           # parte → {"at": quando buscou, "fail": última falha, "data": ...}
_fx_lock = threading.Lock()
_fx_loaded = False


def _fx_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": NEWS_USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=FX_TIMEOUT) as r:
        return json.loads(r.read(512 * 1024))


def _fx_fetch_live() -> dict:
    # Dólar e Euro na MESMA chamada (0.15.0: o Euro entra na página de indicadores do rodapé)
    d = _fx_json("https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL")
    q, e = d["USDBRL"], d.get("EURBRL")
    out = {"bid": float(q["bid"]), "pct": float(q["pctChange"]), "high": float(q["high"]),
           "low": float(q["low"]), "ts": int(q["timestamp"])}
    if e:
        out["eur"] = {"bid": float(e["bid"]), "pct": float(e["pctChange"])}
    return out


# ─── Indicadores econômicos do Banco Central (0.15.0) ─────────────────────────
# Séries do SGS (api.bcb.gov.br, grátis, sem chave). Cada uma: (código, como ler).
#   Selic meta (432, % a.a.) · CDI (4389, % a.a.) · IPCA 12 meses (13522, %) ·
#   IGP-M 12 meses (189 = variação MENSAL; acumulamos os últimos 12 meses) · Salário mínimo (1619, R$)
# Pegadinhas vistas em 19/11/2026:
#   • "…/ultimos/N" às vezes responde HTTP 304 com corpo vazio (cache do CDN deles). A consulta por
#     PERÍODO (dataInicial/dataFinal) respondeu 200 em todos os testes — por isso é a usada.
#   • A Selic meta e o salário mínimo vêm com datas FUTURAS (até a próxima reunião do Copom / o valor já
#     aprovado para o ano seguinte). Terminar o período em HOJE pega o valor vigente.
# Muda no máximo 1×/dia: cache de FX_TTL_IND (6 h) em data/fx_cache.json, junto com a cotação.
FX_TTL_IND = 6 * 3600
BCB_SERIES = {"selic": 432, "cdi": 4389, "ipca12": 13522, "igpm": 189, "salmin": 1619}


def _bcb_series(code: int, days: int) -> list:
    hoje = _date.today()
    q = urllib.parse.urlencode({"formato": "json", "dataInicial": (hoje - _timedelta(days=days)).strftime("%d/%m/%Y"),
                                "dataFinal": hoje.strftime("%d/%m/%Y")})
    rows = _fx_json(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados?{q}")
    return [(r["data"], float(r["valor"])) for r in rows if r.get("valor") not in (None, "")]


def _fx_fetch_ind() -> dict:
    out, errors = {}, []
    plan = {"selic": 20, "cdi": 20, "ipca12": 120, "igpm": 430, "salmin": 400}   # dias para trás em cada consulta
    for key, days in plan.items():
        try:
            rows = _bcb_series(BCB_SERIES[key], days)
            if not rows:
                continue
            if key == "igpm":                              # acumula os últimos 12 meses (juros compostos)
                last12 = rows[-12:]
                acc = 1.0
                for _, v in last12:
                    acc *= 1 + v / 100
                out[key] = {"v": round((acc - 1) * 100, 2), "date": last12[-1][0], "months": len(last12)}
            else:
                out[key] = {"v": rows[-1][1], "date": rows[-1][0]}
        except Exception as e:
            errors.append(f"{key}: {e}")
        time.sleep(.4)                                     # educado com a API (várias seguidas davam erro)
    if not out:
        raise RuntimeError("; ".join(errors) or "sem dados")
    if errors:
        print(f"[indicadores] parcial: {'; '.join(errors)}")
    return out


def _fx_fetch_spark() -> list:
    rows = _fx_json("https://economia.awesomeapi.com.br/json/daily/USD-BRL/30")
    pts = sorted(((int(r["timestamp"]), float(r["bid"])) for r in rows), key=lambda p: p[0])
    by_day: dict[str, float] = {}
    for ts, v in pts:                       # um ponto por dia (o último do dia)
        by_day[datetime.fromtimestamp(ts).strftime("%Y-%m-%d")] = v
    return [{"d": d, "v": v} for d, v in sorted(by_day.items())]


def _fx_fetch_ptax() -> dict:
    end = _date.today()
    start = end - _timedelta(days=10)       # 10 dias cobre feriado prolongado
    url = ("https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarPeriodo("
           "dataInicial=@i,dataFinalCotacao=@f)?" + urllib.parse.urlencode(
               {"@i": f"'{start:%m-%d-%Y}'", "@f": f"'{end:%m-%d-%Y}'", "$format": "json",
                "$select": "cotacaoVenda,dataHoraCotacao"}))
    rows = _fx_json(url)["value"]
    last = max(rows, key=lambda r: r["dataHoraCotacao"])
    return {"sell": float(last["cotacaoVenda"]), "date": last["dataHoraCotacao"][:10]}


def _fx_part(name: str, fetch, ttl: int, force: bool = False):
    """Devolve o dado guardado se ainda vale; senão busca. Falhou: devolve o antigo (ou None)."""
    global _fx_loaded
    with _fx_lock:
        if not _fx_loaded:
            _fx_loaded = True
            try:
                _fx.update(json.loads(FX_CACHE_FILE.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass
        part = _fx.get(name) or {}
    now = time.time()
    fresh = part.get("data") is not None and now - part.get("at", 0) < ttl
    waiting = now - part.get("fail", 0) < FX_RETRY            # falhou há pouco: não insiste
    if (fresh and not force) or (waiting and not force):
        return part.get("data")
    try:
        data = fetch()
    except Exception as e:
        print(f"[cotação] {name}: {e}")
        with _fx_lock:
            _fx[name] = dict(part, fail=now)
        return part.get("data")
    with _fx_lock:
        _fx[name] = {"at": now, "fail": 0, "data": data}
        try:
            tmp = FX_CACHE_FILE.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
            tmp.write_text(json.dumps(_fx, ensure_ascii=False), encoding="utf-8")
            tmp.replace(FX_CACHE_FILE)
        except OSError:
            pass
    return data


def get_fx(force: bool = False) -> dict:
    """Tudo que o rodapé precisa. Campos ausentes = sem dado ainda (a tela esconde aquele pedaço)."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as ex:      # em paralelo: no pior caso espera FX_TIMEOUT, não 4×
        f_live = ex.submit(_fx_part, "live", _fx_fetch_live, FX_TTL_LIVE, force)
        f_spark = ex.submit(_fx_part, "spark", _fx_fetch_spark, FX_TTL_SLOW, force)
        f_ptax = ex.submit(_fx_part, "ptax", _fx_fetch_ptax, FX_TTL_SLOW, force)
        f_ind = ex.submit(_fx_part, "ind", _fx_fetch_ind, FX_TTL_IND, force)
    live, spark, ptax, ind = f_live.result(), list(f_spark.result() or []), f_ptax.result(), f_ind.result()
    out = {"ok": bool(live)}
    if live:
        day = datetime.fromtimestamp(live["ts"]).strftime("%Y-%m-%d")
        if spark and spark[-1]["d"] == day:
            spark[-1] = {"d": day, "v": live["bid"]}       # hoje = valor ao vivo
        elif spark and spark[-1]["d"] < day:
            spark.append({"d": day, "v": live["bid"]})
        out.update(live, day=day, today=day == _date.today().isoformat(),
                   at=datetime.fromtimestamp(live["ts"]).strftime("%H:%M"))
    out["spark"] = spark[-30:]
    if ptax:
        out["ptax"] = ptax
    if ind:
        out["ind"] = ind                                   # Selic, CDI, IPCA 12m, IGP-M 12m, salário mínimo
    return out


@app.get("/api/fx")
def api_fx():
    return get_fx()


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
    per = _num(s.get("today_per_card"), TODAY_SECONDS_PER_CARD, 5, 120)
    return {"enabled": s.get("today_auto") == "1", "start": s.get("today_start") or "08:00",
            "end": s.get("today_end") or "18:00", "every_min": _num(s.get("today_every"), 30, 5, 240),
            # 0.14.0: tempo POR CARD (o player multiplica pela quantidade de cards do dia).
            # "duration" fica para players antigos (0.13.0), que ainda leem o tempo total.
            "per_card": per, "duration": _num(s.get("today_duration"), 15, 5, 120)}


# "Hoje é dia" (0.14.0): cada card (data comemorativa, feriado, "faltam N dias") fica este tempo na tela.
# Antes eram 8 s fixos dentro de um item de 15 s: em dia com 2 cards, eles trocavam rápido demais.
# Por item: config.per_card. Curiosidades automáticas: Configurações → today_per_card.
# O tempo do item na TV = segundos por card × cards de hoje (calculado no player, ver run()).
TODAY_SECONDS_PER_CARD = 30


# ─── Agenda fiscal (0.17.0) ───────────────────────────────────────────────────
#
# Item "fiscal": a TV mostra os vencimentos dos próximos config.days dias (padrão 10), agrupados por data,
# com "HOJE" / "AMANHÃ" / "EM N DIAS" e a nota quando o prazo mudou por feriado ou fim de semana.
# As regras ficam em FISCAL_RULES (conferidas em 19/11/2026; a DCTFWeb passou a vencer no último dia útil
# do mês seguinte pela IN RFB 2.248/2025). Dia útil = segunda a sexta, menos os feriados NACIONAIS
# (BrasilAPI, a mesma lista do "Hoje é dia"; sem internet, FISCAL_FIXED_HOLIDAYS). Feriado municipal não entra.
#   "adjust": "prev" → caiu em dia não útil, ANTECIPA (FGTS, INSS, IRRF, PIS/Cofins, eSocial, Reinf…)
#             "next" → PRORROGA para o próximo dia útil (DAS do Simples e DAS-MEI)
#   "last_bd"         → último dia útil do mês (DCTFWeb, IRPJ/CSLL, ECD, ECF, IRPF)
#   "nth_bd" + "sat"  → N-ésimo dia útil, contando sábado (salários: 5º dia útil, art. 459 da CLT)
#   "month"           → regra anual (só naquele mês)
# Por item: config.rules (ids ligados; sem a chave = FISCAL_DEFAULT_ON), config.custom (linhas próprias,
# ver _fiscal_custom), config.per_page (segundos por página quando não cabe numa tela).
# ── ONDE AJUSTAR UM PRAZO ── só nesta tabela.
FISCAL_RULES = [
    {"id": "esocial", "name": "eSocial — folha (eventos periódicos)", "who": "Competência do mês anterior", "day": 15, "adjust": "prev"},
    {"id": "reinf", "name": "EFD-Reinf", "who": "Retenções e CPRB do mês anterior", "day": 15, "adjust": "prev"},
    {"id": "salario", "name": "Pagamento de salários", "who": "5º dia útil (sábado conta)", "nth_bd": 5, "sat": True},
    {"id": "fgts", "name": "FGTS Digital", "who": "Guia do mês anterior", "day": 20, "adjust": "prev"},
    {"id": "inss", "name": "INSS — contribuições previdenciárias", "who": "DARF da DCTFWeb", "day": 20, "adjust": "prev"},
    {"id": "irrf", "name": "IRRF — salários e serviços", "who": "DARF do mês anterior", "day": 20, "adjust": "prev"},
    {"id": "das", "name": "DAS e PGDAS-D — Simples Nacional", "who": "Empresas do Simples", "day": 20, "adjust": "next"},
    {"id": "mei", "name": "DAS-MEI", "who": "Microempreendedor individual", "day": 20, "adjust": "next"},
    {"id": "piscofins", "name": "PIS e Cofins", "who": "Lucro real e presumido", "day": 25, "adjust": "prev"},
    {"id": "dctfweb", "name": "DCTFWeb — entrega", "who": "Declaração do mês anterior", "last_bd": True},
    {"id": "irpj", "name": "IRPJ e CSLL", "who": "Estimativa mensal / cota trimestral", "last_bd": True},
    {"id": "defis", "name": "DEFIS", "who": "Simples Nacional — anual", "month": 3, "day": 31, "adjust": "prev"},
    {"id": "irpf", "name": "Declaração do IRPF", "who": "Pessoa física — confira o ato do ano", "month": 5, "last_bd": True},
    {"id": "dasn", "name": "DASN-SIMEI", "who": "MEI — declaração anual", "month": 5, "day": 31, "adjust": "prev"},
    {"id": "ecd", "name": "ECD — Escrituração Contábil Digital", "who": "Anual — confira o ato do ano", "month": 5, "last_bd": True},
    {"id": "ecf", "name": "ECF — Escrituração Contábil Fiscal", "who": "Anual", "month": 7, "last_bd": True},
    {"id": "13a", "name": "13º salário — 1ª parcela", "who": "Empregadores", "month": 11, "day": 30, "adjust": "prev"},
    {"id": "13b", "name": "13º salário — 2ª parcela", "who": "Empregadores", "month": 12, "day": 20, "adjust": "prev"},
]
FISCAL_DEFAULT_ON = [r["id"] for r in FISCAL_RULES]
FISCAL_DAYS = 10
FISCAL_FIXED_HOLIDAYS = {"01-01": "Confraternização mundial", "04-21": "Tiradentes", "05-01": "Dia do trabalho",
                         "09-07": "Independência do Brasil", "10-12": "Nossa Senhora Aparecida", "11-02": "Finados",
                         "11-15": "Proclamação da República", "11-20": "Dia da consciência negra", "12-25": "Natal"}


def _fiscal_holidays(years) -> dict[str, str]:
    out = {}
    for y in years:
        got = {h["date"]: h["name"] for h in holidays(y) if h.get("name") != "Páscoa"}
        out.update(got or {f"{y}-{k}": v for k, v in FISCAL_FIXED_HOLIDAYS.items()})
    return out


def _fiscal_custom(text: str) -> tuple[list[dict], list[str]]:
    """Linhas próprias do item: "Nome | dia | regra" (regra = antecipa, prorroga ou nada).
      ISS Rio | 10 | prorroga          → todo mês, dia 10
      Alvará | 31/01 | antecipa        → todo ano, 31 de janeiro
      Balancete | último dia útil      → todo mês, último dia útil
    """
    import re
    rules, errors = [], []
    for n, line in enumerate(str(text or "").splitlines(), 1):
        parts = [p.strip() for p in line.split("|")]
        if not parts[0] or parts[0].startswith("#"):
            continue
        if len(parts) < 2:
            errors.append(f"linha {n}: use Nome | dia | regra"); continue
        r = {"id": f"custom{n}", "name": parts[0][:80], "who": "", "custom": True}
        adj = _plain(parts[2]) if len(parts) > 2 else ""
        r["adjust"] = "prev" if adj.startswith("antecip") else "next" if adj.startswith("prorrog") else "none"
        when = _plain(parts[1])                          # _plain tira a "/": a data usa o texto original
        m = re.fullmatch(r"(\d{1,2})\s*/\s*(\d{1,2})", parts[1].strip())
        if "ultimo dia util" in when:
            r["last_bd"] = True
        elif m and 1 <= int(m[2]) <= 12 and 1 <= int(m[1]) <= 31:
            r.update(day=int(m[1]), month=int(m[2]))
        elif when.isdigit() and 1 <= int(when) <= 31:
            r["day"] = int(when)
        else:
            errors.append(f"linha {n}: não entendi o dia '{parts[1]}' (use 10, 31/01 ou último dia útil)"); continue
        rules.append(r)
    return rules, errors


def _fiscal_date(rule: dict, year: int, month: int, hol: dict):
    """(data do vencimento, data original se mudou) para a regra naquele mês, ou None."""
    import calendar
    from datetime import date, timedelta
    if rule.get("month") and rule["month"] != month:
        return None
    last = calendar.monthrange(year, month)[1]
    bd = lambda d, sat=False: (d.weekday() < 5 or (sat and d.weekday() == 5)) and d.isoformat() not in hol
    if rule.get("last_bd"):
        d = date(year, month, last)
        while not bd(d):
            d -= timedelta(days=1)
        return d, None
    if rule.get("nth_bd"):
        d, n = date(year, month, 1), 0
        while True:
            if bd(d, rule.get("sat")):
                n += 1
                if n == rule["nth_bd"]:
                    return d, None
            d += timedelta(days=1)
    orig = date(year, month, min(rule["day"], last))
    d, step = orig, {"prev": -1, "next": 1}.get(rule.get("adjust"), 0)
    while step and not bd(d):
        d += timedelta(days=step)
    return d, (orig if d != orig else None)


def fiscal_upcoming(cfg: dict, start=None) -> dict:
    """Vencimentos de hoje até hoje + config.days, em ordem de data."""
    from datetime import date, timedelta
    start = start or date.today()
    days = _num(cfg.get("days"), FISCAL_DAYS, 1, 60)
    end = start + timedelta(days=days)
    on = cfg.get("rules") if isinstance(cfg.get("rules"), list) else FISCAL_DEFAULT_ON
    custom, errors = _fiscal_custom(cfg.get("custom", ""))
    rules = [r for r in FISCAL_RULES if r["id"] in on] + custom
    hol = _fiscal_holidays(range(start.year - 1, end.year + 2))
    out, y, m = [], start.year, start.month
    if m == 1:
        y, m = y - 1, 12
    else:
        m -= 1                                    # começa no mês anterior: prorrogação pode cair neste
    while (y, m) <= (end.year, end.month):
        for r in rules:
            got = _fiscal_date(r, y, m, hol)
            if not got or not (start <= got[0] <= end):
                continue
            d, orig = got
            why = ""
            if orig:
                why = (f"{orig.day:02d}/{orig.month:02d} é feriado ({hol[orig.isoformat()]})" if orig.isoformat() in hol
                       else f"{orig.day:02d}/{orig.month:02d} cai num {WEEKDAYS_PT[orig.weekday()]}")
                why = ("Antecipado: " if d < orig else "Prorrogado: ") + why
            out.append({"id": r["id"], "name": r["name"], "who": r.get("who", ""), "date": d.isoformat(),
                        "in_days": (d - start).days, "weekday": WEEKDAYS_PT[d.weekday()], "note": why,
                        "custom": bool(r.get("custom"))})
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    out.sort(key=lambda x: (x["date"], x["custom"], x["name"]))
    return {"start": start.isoformat(), "end": end.isoformat(), "days": days, "items": out, "errors": errors}


@app.get("/api/fiscal/rules")
def fiscal_rules():
    """Lista para o painel montar os liga/desliga do item."""
    return {"rules": FISCAL_RULES, "default_on": FISCAL_DEFAULT_ON, "days": FISCAL_DAYS}


@app.post("/api/fiscal-test", dependencies=[Depends(require_auth)])
async def fiscal_test(request: Request):
    """Painel: mostra a lista que vai para a TV com a configuração digitada (antes de salvar)."""
    return await asyncio.to_thread(fiscal_upcoming, await request.json())


@app.get("/view/fiscal/{item_id}")
def view_fiscal(item_id: str):
    """Tela da agenda fiscal. Datas agrupadas; se não couber, troca de página a cada config.per_page s.
    Recarrega sozinha a cada 30 min (vira o dia sem precisar do player)."""
    cfg = _item_config(item_id)
    data = json.dumps(fiscal_upcoming(cfg), ensure_ascii=False).replace("</", "<\\/")
    title = html.escape(str(cfg.get("title") or "Agenda fiscal"))
    per = _num(cfg.get("per_page"), 15, 5, 120)
    return HTMLResponse(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:100%;height:100%;overflow:hidden;background:#0b1120;color:#f1f5f9;font-family:'Segoe UI',system-ui,sans-serif}}
body{{background:radial-gradient(120% 120% at 15% 0%,#132a52 0%,#0b1120 60%)}}
.top{{position:fixed;top:0;left:0;right:0;height:11vh;display:flex;align-items:center;justify-content:space-between;padding:0 4vw}}
.brand{{display:flex;align-items:center;gap:1.6vw}}
.logo{{height:clamp(26px,4.2vh,72px);opacity:.9}}
.sep{{width:2px;height:4.4vh;border-radius:2px;background:#38bdf8;opacity:.55}}
h1{{font-size:3.4vh;font-weight:700;letter-spacing:.32em;text-transform:uppercase;color:#38bdf8}}
.clock{{font-size:4.2vh;font-weight:300;font-variant-numeric:tabular-nums;opacity:.85}}
.sub{{position:fixed;top:11vh;left:4vw;font-size:2.4vh;color:#94a3b8;letter-spacing:.04em}}
.list{{position:fixed;top:16vh;bottom:9vh;left:4vw;right:4vw;display:flex;flex-direction:column;gap:1.6vh;transition:opacity .5s}}
.list.out{{opacity:0}}
.day{{display:grid;grid-template-columns:13vh 1fr;gap:2.4vw;align-items:start;padding:1.6vh 2vw;border-radius:1.8vh;
  background:rgba(148,163,184,.08);border:1px solid rgba(148,163,184,.14)}}
.day.today{{background:rgba(239,68,68,.14);border-color:rgba(248,113,113,.55)}}
.day.tomorrow{{background:rgba(245,158,11,.12);border-color:rgba(251,191,36,.45)}}
.date{{text-align:center;line-height:1}}
.date b{{display:block;font-size:6.4vh;font-weight:800}}
.date span{{display:block;font-size:2vh;letter-spacing:.14em;text-transform:uppercase;color:#94a3b8;margin-top:.6vh}}
.ob{{display:flex;align-items:baseline;gap:1.4vw;padding:.6vh 0}}
.ob + .ob{{border-top:1px solid rgba(148,163,184,.12)}}
.ob .n{{font-size:3.4vh;font-weight:700}}
.ob .w{{font-size:2.3vh;color:#94a3b8}}
.ob .note{{font-size:2.1vh;color:#fbbf24;margin-left:auto;white-space:nowrap}}
.pill{{display:inline-block;font-size:1.9vh;font-weight:800;letter-spacing:.12em;padding:.5vh 1.2vh;border-radius:.8vh;margin-bottom:.8vh;
  background:#334155;color:#e2e8f0}}
.today .pill{{background:#ef4444;color:#fff}}
.tomorrow .pill{{background:#f59e0b;color:#1c1206}}
.empty{{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2vh;font-size:4.4vh;color:#cbd5e1;text-align:center}}
.empty small{{font-size:2.6vh;color:#94a3b8}}
.foot{{position:fixed;left:4vw;right:4vw;bottom:3.5vh;display:flex;justify-content:space-between;font-size:2vh;color:#64748b}}
</style></head><body>
<div class="top"><div class="brand"><img class="logo" src="/assets/watermark.png" alt="Alava"><span class="sep"></span><h1>{title}</h1></div>
  <div class="clock" id="clock"></div></div>
<div class="sub" id="sub"></div>
<div class="list" id="list"></div>
<div class="foot"><span>Prazos federais e trabalhistas · confira sempre a agenda oficial da Receita Federal</span><span id="page"></span></div>
<script>
const F = {data}, PER = {per} * 1000;
const $ = id => document.getElementById(id), pad = n => String(n).padStart(2, '0');
const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;');
const MES = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
function tick() {{ const d = new Date(); $('clock').textContent = pad(d.getHours()) + ':' + pad(d.getMinutes()); }}
tick(); setInterval(tick, 1000);
const e = F.end.split('-');
$('sub').textContent = `Vencimentos dos próximos ${{F.days}} dias (até ${{e[2]}}/${{e[1]}})`;
// Agrupa por data e divide em páginas de até MAX_OBS obrigações (cabe na TV sem cortar)
const MAX_OBS = 7, groups = [];
F.items.forEach(it => {{ const g = groups[groups.length - 1]; if (g && g.date === it.date) g.obs.push(it); else groups.push({{date: it.date, in_days: it.in_days, weekday: it.weekday, obs: [it]}}); }});
const pages = []; let cur = [], n = 0;
groups.forEach(g => {{ if (n && n + g.obs.length > MAX_OBS) {{ pages.push(cur); cur = []; n = 0; }} cur.push(g); n += g.obs.length; }});
if (cur.length) pages.push(cur);
function when(d) {{ return d === 0 ? 'HOJE' : d === 1 ? 'AMANHÃ' : `EM ${{d}} DIAS`; }}
function render(p) {{
  const L = $('list');
  if (!pages.length) {{ L.innerHTML = ''; document.body.insertAdjacentHTML('beforeend',
    `<div class="empty">✅ Nenhum vencimento nos próximos ${{F.days}} dias<small>Bom trabalho!</small></div>`); return; }}
  L.classList.add('out');
  setTimeout(() => {{
    L.innerHTML = pages[p].map(g => {{
      const [y, m, d] = g.date.split('-');
      const cls = g.in_days === 0 ? 'today' : g.in_days === 1 ? 'tomorrow' : '';
      return `<div class="day ${{cls}}"><div class="date"><b>${{d}}</b><span>${{MES[+m - 1]}} · ${{esc(g.weekday.slice(0, 3))}}</span></div>
        <div><span class="pill">${{when(g.in_days)}}</span>${{g.obs.map(o => `<div class="ob"><span class="n">${{esc(o.name)}}</span>
        <span class="w">${{esc(o.who)}}</span>${{o.note ? `<span class="note">${{esc(o.note)}}</span>` : ''}}</div>`).join('')}}</div></div>`;
    }}).join('');
    $('page').textContent = pages.length > 1 ? `${{p + 1}} / ${{pages.length}}` : '';
    L.classList.remove('out');
  }}, 400);
}}
let pg = 0; render(0);
if (pages.length > 1) setInterval(() => {{ pg = (pg + 1) % pages.length; render(pg); }}, PER);
setTimeout(() => location.reload(), 1800000);
</script></body></html>""", headers={"Cache-Control": "no-store"})


# ─── Aviso urgente (0.17.0) ──────────────────────────────────────────────────
#
# Painel → Programação → "📢 Aviso urgente": um texto que passa POR CIMA da programação por N minutos
# ("Reunião às 15h", "Cliente na recepção"). Fica só na memória do servidor (reiniciar encerra o aviso).
# Vai no estado ("urgent") e na assinatura do WebSocket: o player interrompe o item, mostra /view/urgent
# até "until" e depois volta ao item que foi interrompido. "Encerrar" ou "Pular item" tiram o aviso do ar.
URGENT_STYLES = {"alert": ("#f59e0b", "#1c1206", "⚠️", "Atenção"), "urgent": ("#ef4444", "#ffffff", "🚨", "Urgente"),
                 "info": ("#38bdf8", "#0b1120", "📢", "Aviso")}
_urgent: dict = {}


def urgent_active() -> dict | None:
    if _urgent and _urgent["until"] > time.time():
        return _urgent
    return None


@app.post("/api/urgent", dependencies=[Depends(require_auth)])
async def urgent_start(request: Request):
    body = await request.json()
    text = str(body.get("text") or "").strip()[:240]
    if not text:
        raise HTTPException(400, "Escreva o texto do aviso")
    minutes = _num(body.get("minutes"), 5, 1, 120)
    style = body.get("style") if body.get("style") in URGENT_STYLES else "alert"
    _urgent.clear()
    _urgent.update(id=uuid.uuid4().hex[:8], text=text, sub=str(body.get("sub") or "").strip()[:160], style=style,
                   minutes=minutes, started=time.time(), until=time.time() + minutes * 60)
    return {"ok": True, **urgent_public(), "players": len(_players)}


@app.delete("/api/urgent", dependencies=[Depends(require_auth)])
def urgent_stop():
    _urgent.clear()
    return {"ok": True}


def urgent_public() -> dict:
    u = urgent_active()
    if not u:
        return {"urgent": None}
    return {"urgent": {k: u[k] for k in ("id", "text", "sub", "style", "until", "minutes")} |
            {"until_txt": datetime.fromtimestamp(u["until"]).strftime("%H:%M"), "remaining": round(u["until"] - time.time())}}


@app.get("/view/urgent")
def view_urgent():
    u = urgent_active()
    if not u:
        return view_html('<div style="height:100vh;display:flex;align-items:center;justify-content:center;font-size:4vh;'
                         'color:#64748b;background:#0b1120">Aviso encerrado</div>')
    bg, fg, icon, label = URGENT_STYLES[u["style"]]
    text, sub = html.escape(u["text"]), html.escape(u["sub"])
    size = 12 if len(u["text"]) < 40 else 9 if len(u["text"]) < 90 else 6.6 if len(u["text"]) < 160 else 5
    return HTMLResponse(f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:100%;height:100%;overflow:hidden;background:#0b1120;color:#f8fafc;font-family:'Segoe UI',system-ui,sans-serif}}
.band{{position:fixed;left:0;right:0;top:0;height:13vh;background:{bg};color:{fg};display:flex;align-items:center;gap:2vw;padding:0 4vw;
  font-size:5vh;font-weight:800;letter-spacing:.3em;text-transform:uppercase;animation:pulse 2.4s ease-in-out infinite}}
.band img{{height:5.4vh;margin-left:auto;{'filter:brightness(0);' if fg != '#ffffff' else ''}opacity:.85}}
@keyframes pulse{{50%{{filter:brightness(1.18)}}}}
.box{{position:fixed;top:13vh;bottom:9vh;left:6vw;right:6vw;display:flex;flex-direction:column;justify-content:center;gap:4vh}}
.t{{font-size:{size}vh;font-weight:800;line-height:1.1;animation:in .8s ease both}}
.s{{font-size:4.2vh;color:#cbd5e1;line-height:1.35}}
.foot{{position:fixed;left:6vw;right:6vw;bottom:4vh;display:flex;justify-content:space-between;font-size:2.6vh;color:#94a3b8;
  font-variant-numeric:tabular-nums}}
.edge{{position:fixed;left:0;top:13vh;bottom:0;width:1.2vw;background:{bg}}}
@keyframes in{{from{{opacity:0;transform:translateY(4vh)}}to{{opacity:1;transform:none}}}}
</style></head><body>
<div class="band"><span>{icon}</span><span>{label}</span><img src="/assets/watermark.png" alt="Alava"></div>
<div class="edge"></div>
<div class="box"><div class="t">{text}</div>{f'<div class="s">{sub}</div>' if sub else ''}</div>
<div class="foot"><span id="clock"></span><span></span></div>
<script>
const pad = n => String(n).padStart(2, '0');
function tick() {{ const d = new Date(); document.getElementById('clock').textContent = pad(d.getHours()) + ':' + pad(d.getMinutes()); }}
tick(); setInterval(tick, 1000);
</script></body></html>""", headers={"Cache-Control": "no-store"})


# ─── Relatório do que passou na TV (0.17.0) ──────────────────────────────────
#
# Cada vez que o player avisa o que pôs na tela (POST /api/player/now), a linha anterior de play_log é
# fechada (ended + end_reason, que o próprio player manda em "prev_reason") e uma nova é aberta.
# Itens que o player PULOU sem mostrar (Waze fora) chegam por POST /api/player/skipped.
# As manchetes exibidas (POST /api/news-seen) vão para news_log. Guarda REPORT_KEEP_DAYS dias.
# Painel → Relatório: GET /api/report?start=AAAA-MM-DD&end=AAAA-MM-DD e /api/report.csv.
REPORT_KEEP_DAYS = 90
END_REASONS = {"tempo": "Tempo completo", "pulado": "Pulado pelo painel", "voltou": "Voltou pelo painel",
               "programacao": "Mudou a programação", "editado": "Editado no painel", "removido": "Removido/desativado",
               "login": "Site pediu login", "waze": "Waze fora", "video_fim": "Vídeo terminou",
               "urgente": "Aviso urgente", "encerrado": "Encerrado pelo painel", "erro": "Não abriu",
               "interrompido": "Interrompido", "": "Sem informação"}
_play_row: int | None = None      # linha de play_log em exibição agora


def report_prune() -> None:
    limit = (datetime.now() - _timedelta(days=REPORT_KEEP_DAYS)).strftime("%Y-%m-%d")
    try:
        with db() as con:
            con.execute("DELETE FROM play_log WHERE day < ?", (limit,))
            con.execute("DELETE FROM news_log WHERE day < ?", (limit,))
            con.commit()
    except sqlite3.Error as e:
        print(f"[relatório] limpeza: {e}")


def report_log_play(body: dict) -> None:
    """Fecha a linha anterior e abre a do item que entrou agora."""
    global _play_row
    now = time.time()
    try:
        with db() as con:
            if _play_row:
                con.execute("UPDATE play_log SET ended=?, end_reason=? WHERE id=? AND ended IS NULL",
                            (now, str(body.get("prev_reason") or "tempo")[:20], _play_row))
            cur = con.execute(
                "INSERT INTO play_log (day, started, item_id, name, type, source, planned) VALUES (?,?,?,?,?,?,?)",
                (datetime.now().strftime("%Y-%m-%d"), now, body.get("id"), str(body.get("name") or "")[:120],
                 body.get("type"), str(body.get("source") or "")[:80], int(body.get("duration") or 0)))
            _play_row = cur.lastrowid
            con.commit()
    except sqlite3.Error as e:
        print(f"[relatório] {e}")


@app.post("/api/player/skipped")
async def player_skipped(request: Request):
    """O player pulou um item sem mostrar (ex.: Waze fora): entra no relatório com 0 s."""
    if not _is_local(request):
        raise HTTPException(403, "Só o player deste computador informa")
    b = await request.json()
    now = time.time()
    with db() as con:
        con.execute("INSERT INTO play_log (day, started, ended, item_id, name, type, source, planned, end_reason) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (datetime.now().strftime("%Y-%m-%d"), now, now, b.get("id"), str(b.get("name") or "")[:120],
                     b.get("type"), str(b.get("source") or "")[:80], int(b.get("duration") or 0),
                     str(b.get("reason") or "")[:20]))
        con.commit()
    return {"ok": True}


def _report_days(start: str | None, end: str | None) -> tuple[str, str]:
    today = datetime.now().strftime("%Y-%m-%d")
    ok = lambda s: bool(s) and len(s) == 10 and s[4] == "-" and s[7] == "-" and s.replace("-", "").isdigit()
    s = start if ok(start) else today
    e = end if ok(end) else s
    return (s, e) if s <= e else (e, s)


def report_data(start: str | None = None, end: str | None = None) -> dict:
    s, e = _report_days(start, end)
    now = time.time()
    with db() as con:
        rows = [dict(r) for r in con.execute("SELECT * FROM play_log WHERE day BETWEEN ? AND ? ORDER BY started", (s, e))]
        news = [dict(r) for r in con.execute("SELECT * FROM news_log WHERE day BETWEEN ? AND ? ORDER BY at", (s, e))]
    timeline, summary = [], {}
    for r in rows:
        if r["ended"] is None:      # aberta: é a que está no ar agora, ou o servidor reiniciou no meio
            r["ended"] = now if r["id"] == _play_row else r["started"] + (r["planned"] or 0)
            r["end_reason"] = "no_ar" if r["id"] == _play_row else ""
        secs = max(0, round(r["ended"] - r["started"]))
        reason = r["end_reason"] or ""
        timeline.append({"start": datetime.fromtimestamp(r["started"]).strftime("%d/%m %H:%M:%S"), "name": r["name"],
                         "type": r["type"], "source": r["source"], "planned": r["planned"], "seconds": secs,
                         "reason": reason, "reason_txt": "No ar agora" if reason == "no_ar" else END_REASONS.get(reason, reason)})
        k = (r["item_id"] or r["name"], r["type"])
        g = summary.setdefault(k, {"name": r["name"], "type": r["type"], "shows": 0, "seconds": 0, "skipped": 0,
                                   "interrupted": 0, "reasons": {}})
        if secs == 0 and reason in ("waze", "login"):
            g["skipped"] += 1
        else:
            g["shows"] += 1
        g["seconds"] += secs
        if reason not in ("tempo", "no_ar", "video_fim", ""):
            g["interrupted"] += 1
            g["reasons"][END_REASONS.get(reason, reason)] = g["reasons"].get(END_REASONS.get(reason, reason), 0) + 1
    items = sorted(summary.values(), key=lambda g: -g["seconds"])
    return {"start": s, "end": e, "items": items, "timeline": timeline,
            "news": [{"at": datetime.fromtimestamp(n["at"]).strftime("%d/%m %H:%M"), "title": n["title"],
                      "source": n["source"], "item": n["item_name"]} for n in news],
            "totals": {"seconds": sum(g["seconds"] for g in items), "shows": sum(g["shows"] for g in items),
                       "interrupted": sum(g["interrupted"] for g in items), "skipped": sum(g["skipped"] for g in items),
                       "news": len(news), "news_unique": len({n["title"] for n in news})}}


@app.get("/api/report", dependencies=[Depends(require_auth)])
def api_report(start: str | None = None, end: str | None = None):
    return report_data(start, end)


@app.get("/api/report.csv", dependencies=[Depends(require_auth)])
def api_report_csv(start: str | None = None, end: str | None = None, kind: str = "timeline"):
    """Planilha (abre no Excel: separador ";" e acentos em UTF-8 com BOM)."""
    import csv
    import io
    r = report_data(start, end)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    if kind == "news":
        w.writerow(["Quando", "Manchete", "Fonte", "Item"])
        for n in r["news"]:
            w.writerow([n["at"], n["title"], n["source"], n["item"]])
    else:
        w.writerow(["Início", "Item", "Tipo", "Programação", "Previsto (s)", "No ar (s)", "Como terminou"])
        for t in r["timeline"]:
            w.writerow([t["start"], t["name"], t["type"], t["source"], t["planned"], t["seconds"], t["reason_txt"]])
    name = f"alava_tv_{kind}_{r['start']}" + (f"_a_{r['end']}" if r["end"] != r["start"] else "") + ".csv"
    return Response("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


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
                   "wind_speed_10m,wind_gusts_10m,is_day,precipitation,cloud_cover",
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


# ─── Tempo OBSERVADO agora (0.13.0) ───────────────────────────────────────────
#
# O "current" da Open-Meteo NÃO é observação: é o modelo estimando o agora. Em 19/11/2026, às 13h45,
# o modelo padrão (best_match) dizia "Trovoadas" (código 95, por causa de muita energia convectiva e
# 0,2 mm previstos), enquanto os 5 aeroportos do Rio observavam poucas nuvens. Por isso a condição
# atual (ícone, texto e fundo animado) passa a vir do METAR — o boletim oficial de tempo observado que
# todo aeroporto publica de hora em hora (e na hora, se o tempo muda: SPECI). Fonte: aviationweather.gov
# (NOAA, grátis, sem chave). A previsão (7 dias, chance de chuva) continua vindo do modelo.
#
#   METAR_STATION no .env ... código ICAO fixo (ex.: SBJR = Jacarepaguá). Vazio = o mais próximo, sozinho.
#   METAR_MAX_KM ............ distância máxima da estação automática (mais longe que isso, não vale)
#   METAR_MAX_AGE_MIN ....... boletim mais velho que isso é ignorado (volta para o modelo)
# Sem METAR válido: usa o modelo, mas trovoada/chuva com menos de MODEL_STORM_MIN_MM previstos
# vira nublado/parcialmente nublado (_sane_model_code) — era exatamente o caso do fundo de tempestade.
METAR_STATION = os.getenv("METAR_STATION", "").strip().upper()
METAR_MAX_KM = 40
METAR_MAX_AGE_MIN = 100
MODEL_STORM_MIN_MM = 0.5
_metar_last: dict = {"data": None}          # último boletim bom (se a internet falhar, vale enquanto não envelhecer)


def _km(lat1, lon1, lat2, lon2) -> float:
    import math
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2 +
         math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def _metar_code(m: dict) -> int:
    """METAR → código WMO usado pela tela (os mesmos números da Open-Meteo).
    Fenômeno no local (TS, RA, DZ, SN, FG) manda; sem fenômeno, vale a maior cobertura de nuvens.
    "VC…" (nas vizinhanças) e "RE…" (recente, já passou) não contam como tempo no local."""
    tokens = [t for t in (m.get("wxString") or "").upper().split() if not t.startswith(("VC", "RE"))]
    def has(code):
        return next((t for t in tokens if code in t), None)
    if (t := has("TS")):
        return 99 if ("GR" in t or "GS" in t) else 95
    if (t := has("SN")):
        return 75 if t.startswith("+") else 71 if t.startswith("-") else 73
    if (t := has("RA")):
        heavy, light = t.startswith("+"), t.startswith("-")
        if "SH" in t:
            return 82 if heavy else 80 if light else 81
        return 65 if heavy else 61 if light else 63
    if (t := has("DZ")):
        return 55 if t.startswith("+") else 51 if t.startswith("-") else 53
    if any(t in ("FG", "FZFG") for t in tokens):
        return 45
    rank = {"FEW": 1, "SCT": 2, "BKN": 3, "OVC": 3, "OVX": 3}      # SKC/CLR/NSC/CAVOK = 0 (céu limpo)
    covers = [c.get("cover") for c in (m.get("clouds") or [])] + [m.get("cover")]
    return max((rank.get(c, 0) for c in covers), default=0)


def _fetch_metar(lat: float, lon: float) -> dict | None:
    """Boletim mais recente da estação configurada ou da mais próxima. None = nada aproveitável."""
    base = "https://aviationweather.gov/api/data/metar?format=json&hours=3&"
    if METAR_STATION:
        url = base + urllib.parse.urlencode({"ids": METAR_STATION})
    else:
        d = 0.6   # ~65 km para cada lado; depois filtra por METAR_MAX_KM
        url = base + urllib.parse.urlencode({"bbox": f"{lat - d:.3f},{lon - d:.3f},{lat + d:.3f},{lon + d:.3f}"})
    rows = _http_json(url, timeout=8) or []
    now = time.time()
    best = None
    for m in rows:
        try:
            km = _km(lat, lon, float(m["lat"]), float(m["lon"]))
            age = (now - float(m["obsTime"])) / 60
        except (KeyError, TypeError, ValueError):
            continue
        if age > METAR_MAX_AGE_MIN or (not METAR_STATION and km > METAR_MAX_KM):
            continue
        # a mais próxima; entre boletins da mesma estação, o mais novo
        if best is None or (km, age) < (best["km"], best["age_min"]):
            # "Rio de Janeiro/Dumont Arpt, RJ, BR" → "Dumont"; "Jacarepagua Arpt, RJ, BR" → "Jacarepagua"
            short = _re.sub(r"\s+(Arpt|Airport|Intl|Aeroporto|AB)\b.*$", "", str(m.get("name") or "").split(",")[0]).split("/")[-1].strip()
            best = {"station": m.get("icaoId"), "name": f"aeroporto {short} ({m.get('icaoId')})" if short else m.get("icaoId"),
                    "km": round(km, 1), "age_min": round(age), "raw": m.get("rawOb", ""),
                    "time": datetime.fromtimestamp(float(m["obsTime"])).strftime("%H:%M"),
                    "obs_ts": float(m["obsTime"]), "code": _metar_code(m), "temp": m.get("temp"),
                    "dewp": m.get("dewp")}
    return best


def _rh_from_dewpoint(t: float, td: float) -> float:
    """Umidade relativa (%) a partir da temperatura e do ponto de orvalho (fórmula de Magnus)."""
    import math
    a, b = 17.625, 243.04
    return max(1.0, min(100.0, 100 * math.exp(a * td / (b + td) - a * t / (b + t))))


def _heat_index(t: float, rh: float) -> float:
    """Sensação térmica no calor (índice de calor da NOAA, em °C). Abaixo de 27 °C a sensação = temperatura."""
    if t < 27 or rh < 40:
        return t
    f = t * 9 / 5 + 32
    hi = (-42.379 + 2.04901523 * f + 10.14333127 * rh - .22475541 * f * rh - .00683783 * f * f
          - .05481717 * rh * rh + .00122874 * f * f * rh + .00085282 * f * rh * rh - .00000199 * f * f * rh * rh)
    return (hi - 32) * 5 / 9


def _sane_model_code(code: int, precip, clouds) -> int:
    """Sem observação: não deixa o modelo pôr trovoada/chuva na tela quando ele mesmo prevê quase nada de chuva."""
    if code >= 61 and (precip or 0) < MODEL_STORM_MIN_MM:
        return 3 if (clouds or 0) >= 85 else 2
    return code


def _apply_observed(w: dict, lat, lon) -> None:
    """Troca a condição atual do modelo pela observada (METAR). Guarda as duas para conferência."""
    cur = w["current"]
    cur["code_model"] = cur["code"]
    obs = None
    try:
        obs = _fetch_metar(float(lat), float(lon))
        if obs:
            _metar_last["data"] = obs
    except Exception as e:
        print(f"[clima] METAR indisponível: {e}")
    if not obs and _metar_last["data"]:           # sem internet agora: o último boletim ainda vale se for recente
        last = _metar_last["data"]
        age = (time.time() - last["obs_ts"]) / 60
        if age <= METAR_MAX_AGE_MIN:
            obs = dict(last, age_min=round(age))
    if obs:
        cur["code"] = obs["code"]
        cur["source"] = "observado"
        cur["obs"] = {k: obs.get(k) for k in ("station", "name", "km", "time", "age_min", "raw", "temp", "dewp")}
        # Temperatura, umidade e sensação também observadas (pedido de 19/11/2026: o modelo dizia 29°, o
        # aeroporto mediu 33°). A sensação é recalculada (índice de calor) porque a do modelo foi feita
        # para a temperatura do modelo. O vento e a chance de chuva continuam do modelo.
        if obs.get("temp") is not None:
            t = float(obs["temp"])
            cur["temp_model"], cur["humidity_model"], cur["feels_model"] = cur["temp"], cur["humidity"], cur["feels"]
            cur["temp"] = t
            if obs.get("dewp") is not None:
                cur["humidity"] = round(_rh_from_dewpoint(t, float(obs["dewp"])))
            cur["feels"] = round(_heat_index(t, cur["humidity"] or 0), 1)
            today = (w.get("daily") or [None])[0]
            if today:                                   # observado passou da máx./mín. prevista: o dia acompanha
                if today.get("max") is not None and t > today["max"]:
                    today["max"] = t
                if today.get("min") is not None and t < today["min"]:
                    today["min"] = t
    else:
        cur["code"] = _sane_model_code(cur["code"], cur.get("precip"), cur.get("clouds"))
        cur["source"] = "modelo"


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
            "clouds": cur.get("cloud_cover"),
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
        _apply_observed(w, s["weather_lat"], s["weather_lon"])   # condição atual = observada (METAR), 0.13.0
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
    # 0.13.0: o tempo OBSERVADO (METAR) entra como mais uma linha — é o "gabarito" para julgar os modelos.
    obs = _metar_last["data"]
    if obs and (time.time() - obs["obs_ts"]) / 60 <= METAR_MAX_AGE_MIN:
        lines.append(";".join(str(v).replace(".", ",") if isinstance(v, float) else str(v) for v in (
            datetime.fromtimestamp(obs["obs_ts"]).strftime("%Y-%m-%d %H:%M"), f"metar_{obs['station']}",
            obs["temp"] if obs["temp"] is not None else "", obs["code"], obs["code"],
            WX_CODE_PT.get(obs["code"], obs["code"]), "", "", "")) + "\n")
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
        cfgs = [json.loads(r["config"] or "{}") for r in rows]
        for c in cfgs:
            get_news(c, force=True)
        if any(c.get("show_fx", True) for c in cfgs):
            get_fx()          # cotação do rodapé já pronta quando a tela de notícias abrir
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


def traffic_embed(s: dict) -> tuple[str, bool]:
    """Endereço do mapa de trânsito e se o player deve abri-lo DIRETO (fora da nossa página).

    Waze → direto (True). Dentro de um iframe de outro endereço, o Chrome trata o Waze como
    conteúdo de terceiros: bloqueia o cookie de visitante e o reCAPTCHA dele, e o Waze deixa
    de enviar os dados de trânsito (o mapa aparece SEM as linhas coloridas — era o defeito da TV).
    No painel funciona porque o navegador de quem edita aceita esses cookies. Aberto como página
    principal, funciona também na TV; o player desenha por cima a faixa da Alava
    (player.py → TRAFFIC_BAND_JS).
    Google Maps (com MAPS_API_KEY) → dentro da nossa página (False): a API de incorporação funciona em iframe.

    Histórico: corrigido na 0.7.0, mas a correção ficou só na branch fix/transito-waze-no-player e
    nunca entrou na main. Portada para a 0.14.0.
    """
    lat, lon, maps_key = s["weather_lat"], s["weather_lon"], s["maps_api_key"]
    if maps_key:
        return f"https://www.google.com/maps/embed/v1/view?key={maps_key}&center={lat},{lon}&zoom=13&maptype=roadmap", False
    return f"https://embed.waze.com/iframe?zoom=14&lat={lat}&lon={lon}&ct=livemap&pin=1", True


@app.get("/api/traffic")
def api_traffic():
    """Usado pelo player para decidir como abrir o item de trânsito."""
    s = load_settings()
    url, direct = traffic_embed(s)
    city = (s["weather_city"] or "").strip()
    return {"url": url, "direct": direct, "title": "Trânsito agora" + (f" · {city}" if city else "")}


@app.get("/view/traffic")
def view_traffic():
    """Mapa de trânsito com uma faixa no topo: logo Alava à esquerda, título e relógio à direita.

    Usada na pré-visualização do painel e, com Google Maps, também na TV. Com Waze, a TV abre
    o Waze direto (ver traffic_embed); a faixa desenhada pelo player tem o mesmo visual desta.
    O logo fica na faixa (e não por cima do mapa) porque o canto superior esquerdo do Waze
    e do Google Maps já tem a busca/cartão do próprio mapa.
    """
    s = load_settings()
    src, _ = traffic_embed(s)
    city = html.escape(s["weather_city"] or "")
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
    (padrão: TODAY_SECONDS_PER_CARD = 30 s; o player manda ?per= com o valor do item ou das
    Configurações). `?d=AAAA-MM-DD` mostra outro dia, para testar pelo painel.
    """
    info = api_today(d)
    data = json.dumps(info, ensure_ascii=False).replace("</", "<\\/")
    per_ms = _num(per, TODAY_SECONDS_PER_CARD, 3, 120) * 1000
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


# Rodapé da cotação na tela de notícias (0.13.0; indicadores do Banco Central na 0.15.0). Fica ABAIXO da barra
# de tempo dos cards. config.show_fx = página do dólar; config.show_ind = página de indicadores (as duas se alternam).
# Strings comuns (não f-string) para não precisar dobrar as chaves; view_news() injeta as duas.
# Cores: ▲ verde = dólar subiu no dia, ▼ vermelho = caiu (convenção de painel de cotação).
NEWS_FX_CSS = """
body.fx .card{bottom:21vh}
body.fx .bottom{bottom:12.6vh}
body.fx .summary{-webkit-line-clamp:3}
.fx{position:fixed;left:0;right:0;bottom:0;height:9.6vh;
  background:linear-gradient(180deg,rgba(15,23,42,.55),rgba(15,23,42,.96));border-top:.2vh solid rgba(148,163,184,.18);
  font-variant-numeric:tabular-nums;color:#cbd5e1}
/* 0.15.0: duas "páginas" no mesmo rodapé (dólar e indicadores), que se alternam com um esmaecer */
.fxp{position:absolute;inset:0;display:flex;align-items:center;gap:2.4vw;padding:0 4vw;transition:opacity .9s ease}
.fxp.off{opacity:0}
.fx[hidden],.fx .grp[hidden],.fxp[hidden]{display:none}
.fx .grp{display:flex;flex-direction:column;justify-content:center;gap:.5vh;white-space:nowrap}
.fx .lbl{font-size:1.55vh;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#94a3b8}
.fx .big{font-size:3.7vh;font-weight:700;color:#f8fafc;line-height:1}
.fx .chg{font-size:2.7vh;font-weight:700;line-height:1}
.fx .up{color:#4ade80}.fx .down{color:#f87171}.fx .flat{color:#94a3b8}
.fx .mid{font-size:2.3vh;font-weight:600;color:#e2e8f0;line-height:1}
.fx .ind{font-size:3vh;font-weight:700;color:#f8fafc;line-height:1}
.fx .ind small{font-size:1.7vh;font-weight:600;color:#94a3b8;margin-left:.4vw}
.fx svg{display:block;width:15vw;height:3.9vh;overflow:visible}
.fx .vsep{width:1px;align-self:stretch;margin:2.2vh 0;background:rgba(148,163,184,.25)}
.fx .when{margin-left:auto;text-align:right;font-size:1.7vh;line-height:1.5;color:#94a3b8}
"""
NEWS_FX_HTML = """<div class="fx" id="fx" hidden>
 <div class="fxp" id="fx-pa">
  <div class="grp"><span class="lbl">Dólar comercial</span><span class="big" id="fx-bid"></span></div>
  <div class="grp"><span class="lbl" id="fx-chg-lbl">Hoje</span><span class="chg" id="fx-chg"></span></div>
  <div class="grp" id="fx-spark-g"><span class="lbl">Últimos 30 dias</span><svg id="fx-spark"></svg></div>
  <div class="grp"><span class="lbl">Mínima · Máxima do dia</span><span class="mid" id="fx-range"></span></div>
  <div class="vsep"></div>
  <div class="grp" id="fx-ptax-g"><span class="lbl" id="fx-ptax-lbl">PTAX venda · Banco Central</span><span class="mid" id="fx-ptax"></span></div>
  <div class="when"><span id="fx-at"></span><br>AwesomeAPI · Banco Central</div>
 </div>
 <div class="fxp off" id="fx-pb">
  <div class="grp" id="ind-eur-g"><span class="lbl">Euro</span><span class="ind" id="ind-eur"></span></div>
  <div class="vsep"></div>
  <div class="grp" id="ind-selic-g"><span class="lbl">Selic</span><span class="ind" id="ind-selic"></span></div>
  <div class="grp" id="ind-cdi-g"><span class="lbl">CDI</span><span class="ind" id="ind-cdi"></span></div>
  <div class="grp" id="ind-ipca12-g"><span class="lbl" id="ind-ipca12-l">IPCA 12 meses</span><span class="ind" id="ind-ipca12"></span></div>
  <div class="grp" id="ind-igpm-g"><span class="lbl" id="ind-igpm-l">IGP-M 12 meses</span><span class="ind" id="ind-igpm"></span></div>
  <div class="grp" id="ind-salmin-g"><span class="lbl">Salário mínimo</span><span class="ind" id="ind-salmin"></span></div>
  <div class="when">Indicadores econômicos<br>Banco Central · AwesomeAPI</div>
 </div>
</div>"""
NEWS_FX_JS = """
// ─── Rodapé (0.13.0 dólar · 0.15.0 indicadores): desenha FX (embutido e renovado de /api/fx a cada 1 min) ───
// Página A = dólar (comercial, variação, 30 dias, mín/máx, PTAX). Página B = Euro, Selic, CDI, IPCA 12m,
// IGP-M 12m e salário mínimo. Com as duas ligadas, alternam a cada FX_PAGE_MS. Cada uma liga/desliga no item.
// 2 casas decimais (R$ 5,91) em todos os valores — pedido de 19/11/2026; para voltar a 4, troque d = 2 por d = 4
const FX_PAGE_MS = 15000;
const brl = (v, d = 2) => 'R$ ' + v.toLocaleString('pt-BR', {minimumFractionDigits: d, maximumFractionDigits: d});
const pct = v => v.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + '%';
const ddmm = s => s.slice(8, 10) + '/' + s.slice(5, 7);
const MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
const mesAno = br => MES[+br.slice(3, 5) - 1] + '/' + br.slice(8, 10);     // "01/10/2026" → "out/26"
const arrow = p => { const c = Math.abs(p) < 0.005 ? 'flat' : p > 0 ? 'up' : 'down'; return [c, {flat: '■ ', up: '▲ ', down: '▼ '}[c]]; };
function drawSpark(svg, pts, dotColor) {
  const W = svg.clientWidth || 280, H = svg.clientHeight || 56, pad = 6;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  if (!pts || pts.length < 2) { svg.innerHTML = ''; return false; }
  const vs = pts.map(p => p.v), lo = Math.min(...vs), hi = Math.max(...vs), k = (H - 2 * pad) / ((hi - lo) || 1);
  const xy = pts.map((p, i) => [pad + i * (W - 2 * pad) / (pts.length - 1), H - pad - (p.v - lo) * k]);
  const line = 'M' + xy.map(q => q[0].toFixed(1) + ' ' + q[1].toFixed(1)).join(' L');
  const last = xy[xy.length - 1];
  svg.innerHTML = `<defs><linearGradient id="fxg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${ACC}" stop-opacity=".32"/><stop offset="1" stop-color="${ACC}" stop-opacity="0"/></linearGradient></defs>
    <path d="${line} L${last[0].toFixed(1)} ${H} L${xy[0][0].toFixed(1)} ${H} Z" fill="url(#fxg)"/>
    <path d="${line}" fill="none" stroke="${ACC}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${last[0]}" cy="${last[1]}" r="9" fill="${dotColor}" opacity=".25"><animate attributeName="r" values="6;12;6" dur="2.4s" repeatCount="indefinite"/></circle>
    <circle cx="${last[0]}" cy="${last[1]}" r="5" fill="${dotColor}"/>`;
  return true;
}
// Quais páginas têm o que mostrar agora (ligadas no item E com dado)
const fxPages = () => [SHOW_FX && FX && FX.ok && 'fx-pa', SHOW_IND && FX && (FX.ind || FX.eur) && 'fx-pb'].filter(Boolean);
let fxPage = 0;
function showFxPage() {
  const ps = fxPages(), on = ps[fxPage % Math.max(1, ps.length)];
  ['fx-pa', 'fx-pb'].forEach(id => { $(id).hidden = !ps.includes(id); $(id).classList.toggle('off', id !== on); });
}
function drawFx() {
  const ps = fxPages();
  $('fx').hidden = !ps.length; document.body.classList.toggle('fx', !!ps.length);
  if (!ps.length) return;
  if (ps.includes('fx-pa')) {
    const [cls, ar] = arrow(FX.pct);
    $('fx-bid').textContent = brl(FX.bid);
    $('fx-chg').className = 'chg ' + cls;
    $('fx-chg').textContent = ar + pct(Math.abs(FX.pct));
    // fim de semana/feriado: a API devolve o último pregão — a etiqueta deixa isso claro
    $('fx-chg-lbl').textContent = FX.today ? 'Variação hoje' : 'Pregão de ' + ddmm(FX.day);
    $('fx-range').textContent = brl(FX.low) + '  ·  ' + brl(FX.high);
    $('fx-spark-g').hidden = !drawSpark($('fx-spark'), FX.spark, {up: '#4ade80', down: '#f87171', flat: '#94a3b8'}[cls]);
    $('fx-ptax-g').hidden = !FX.ptax;
    if (FX.ptax) { $('fx-ptax-lbl').textContent = 'PTAX venda · BCB · ' + ddmm(FX.ptax.date); $('fx-ptax').textContent = brl(FX.ptax.sell); }
    $('fx-at').textContent = 'Cotação das ' + FX.at;
  }
  if (ps.includes('fx-pb')) {
    const I = FX.ind || {}, set = (k, html, lbl) => {
      $(`ind-${k}-g`).hidden = !html;
      if (html) $(`ind-${k}`).innerHTML = html;
      if (lbl && $(`ind-${k}-l`)) $(`ind-${k}-l`).textContent = lbl;
    };
    if (FX.eur) { const [c, ar] = arrow(FX.eur.pct); set('eur', `${brl(FX.eur.bid)}<small class="${c}">${ar}${pct(Math.abs(FX.eur.pct))}</small>`); }
    else set('eur', '');
    set('selic', I.selic && `${pct(I.selic.v)}<small>a.a.</small>`);
    set('cdi', I.cdi && `${pct(I.cdi.v)}<small>a.a.</small>`);
    set('ipca12', I.ipca12 && pct(I.ipca12.v), I.ipca12 && 'IPCA 12 meses · ' + mesAno(I.ipca12.date));
    set('igpm', I.igpm && pct(I.igpm.v), I.igpm && 'IGP-M 12 meses · ' + mesAno(I.igpm.date));
    set('salmin', I.salmin && brl(I.salmin.v));
  }
  showFxPage();
}
drawFx();
if (SHOW_FX || SHOW_IND) {
  setInterval(async () => { try { FX = await (await fetch('/api/fx')).json(); drawFx(); } catch (e) {} }, 60000);
  setInterval(() => { fxPage++; showFxPage(); }, FX_PAGE_MS);
}
"""


@app.get("/view/news/{item_id}")
def view_news(item_id: str, tv: int = 0):
    """Tela de notícias: uma manchete por vez (foto + título + resumo), trocando a cada
    config.per_headline segundos. Começa já com as manchetes embutidas (sem "Carregando…")
    e atualiza sozinha a cada 5 min.
    tv=1 (0.16.0, só o player usa): o pacote vem sem as já exibidas e cada card que fica 3 s (SEEN_AFTER, no JS)
    na tela é anotado (POST /api/news-seen). Sem tv=1 (prévia do painel) continua como antes:
    guarda no navegador em qual manchete parou e não anota nada.
    window.newsNav(-1 | 1) (0.16.0): volta / avança um card (botões do painel, via player).
    """
    cfg = _item_config(item_id)
    tv_js = "true" if tv else "false"
    with db() as con:                     # 0.17.0: nome do item, para o relatório das manchetes
        row = con.execute("SELECT name FROM items WHERE id=?", (item_id,)).fetchone()
    item_name_js = json.dumps(row["name"] if row else "", ensure_ascii=False).replace("</", "<\\/")
    data = json.dumps(get_news(cfg, tv=bool(tv)), ensure_ascii=False).replace("</", "<\\/")
    title = html.escape(str(cfg.get("title") or "Notícias"))
    accent = _css_color(cfg.get("accent"), "#38bdf8")
    per = _num(cfg.get("per_headline"), NEWS_SECONDS_PER_CARD, 4, 120)   # padrão 30 s por card (0.13.0)
    show_img = "true" if cfg.get("show_images", True) else "false"
    # Logo Alava no cabeçalho (0.11.0; config.show_logo, ligado por padrão).
    # Usa assets/watermark.png (versão branca, fundo transparente): é a de melhor contraste
    # no fundo azul-escuro desta tela. As outras (minimalista azul-marinho e "fundo branco")
    # sumiriam no fundo escuro. Mesmo tamanho do logo das telas de clima e trânsito.
    logo = ('<img class="logo" src="/assets/watermark.png" alt="Alava"><span class="sep"></span>'
            if cfg.get("show_logo", True) else "")
    # Rodapé com a cotação do dólar (config.show_fx, ligado por padrão). Sem dado (sem internet e sem
    # cache), o rodapé some e o cartão volta a ocupar a tela toda.
    show_fx = bool(cfg.get("show_fx", True))
    show_ind = bool(cfg.get("show_ind", True))          # 0.15.0: página de indicadores (Euro, Selic, CDI, IPCA…)
    fx_data = json.dumps(get_fx(), ensure_ascii=False) if (show_fx or show_ind) else "null"
    show_fx_js = "true" if show_fx else "false"
    show_ind_js = "true" if show_ind else "false"
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
/* Matéria sem foto (0.13.0): fundo azul-escuro com a logo Alava no centro, no lugar de um quadro vazio */
.pic.brand{{background:url('/assets/watermark.png') center/46% auto no-repeat,linear-gradient(135deg,#17325f,#0b1120 70%)}}
/* Selo FONTE • CATEGORIA (0.13.0). Preferencial / foco contábil = selo cheio na cor de destaque;
   as demais fontes = só contorno. Tamanho pensado para ler da outra ponta da sala. */
.tag{{display:inline-block;max-width:100%;font-size:2.5vh;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  padding:.9vh 1.8vh;border-radius:1vh;border:.25vh solid {accent};color:{accent};margin-bottom:2vh;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.tag.pref{{background:{accent};color:#0b1120}}
.tag[hidden]{{display:none}}
.meta{{font-size:2.4vh;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:{accent};margin-bottom:2.6vh}}
.meta:empty{{display:none}}
.headline{{font-size:6vh;font-weight:700;line-height:1.14;display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}}
.card.noimg .headline{{font-size:7.6vh}}
.summary{{margin-top:3vh;font-size:3vh;line-height:1.4;color:#cbd5e1;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}}
.bottom{{position:fixed;left:4vw;right:4vw;bottom:4.5vh;display:flex;align-items:center;gap:2vw;font-size:2.2vh;color:#94a3b8;
  font-variant-numeric:tabular-nums}}
.bar{{flex:1;height:.6vh;border-radius:1vh;background:rgba(148,163,184,.25);overflow:hidden}}
.bar i{{display:block;height:100%;width:0;background:{accent}}}
.empty{{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;font-size:4vh;color:#94a3b8;text-align:center}}
{NEWS_FX_CSS}
</style></head>
<body>
<div class="top"><div class="brand">{logo}<h1>{title}</h1></div><div class="clock" id="clock"></div></div>
<div class="card" id="card"><div class="pic" id="pic"></div>
  <div><div class="tag" id="tag" hidden></div><div class="meta" id="meta"></div><div class="headline" id="headline"></div><div class="summary" id="summary"></div></div></div>
<div class="bottom"><span id="count"></span><div class="bar"><i id="bar"></i></div></div>
{NEWS_FX_HTML}
<script>
let N = {data}, FX = {fx_data};
const PER = {per} * 1000, SHOW_IMG = {show_img}, KEY = 'news-idx-{html.escape(item_id)}';
const SHOW_FX = {show_fx_js}, SHOW_IND = {show_ind_js}, ACC = '{accent}';
const TV = {tv_js}, SEEN_AFTER = 3000, ITEM_ID = {json.dumps(item_id)}, ITEM_NAME = {item_name_js};   // 0.16.0: na TV, o card que ficou 3 s na tela conta como exibido
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
// idx = próximo card a mostrar; cur = o que está na tela. Na TV começa sempre do 1º: o pacote já vem
// sem as manchetes exibidas. Na prévia, continua de onde parou (localStorage), como antes da 0.16.0.
let idx = 0, cur = 0, picToken = 0, seenTimer = 0, timer = 0;
if (!TV) {{ try {{ idx = parseInt(localStorage.getItem(KEY)) || 0; }} catch (e) {{}} }}
function markSeen(it) {{
  clearTimeout(seenTimer);
  if (!TV) return;
  seenTimer = setTimeout(() => fetch('/api/news-seen', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{title: it.title, link: it.link || '', source: it.source || '', item_id: ITEM_ID, item_name: ITEM_NAME}})}}).catch(() => {{}}), SEEN_AFTER);
}}
function show(target) {{
  const list = (N && N.items) || [];
  if (!list.length) {{
    if (!document.querySelector('.empty'))
      document.body.insertAdjacentHTML('beforeend', '<div class="empty">Sem notícias no momento.<br>Confira os endereços dos feeds no painel.</div>');
    $('card').hidden = true; return;
  }}
  const i = (((target ?? idx) % list.length) + list.length) % list.length;
  cur = i; idx = i + 1;
  try {{ if (!TV) localStorage.setItem(KEY, idx % list.length); }} catch (e) {{}}
  const it = list[i];
  markSeen(it);
  $('card').classList.add('out');
  setTimeout(() => {{
    const img = SHOW_IMG && it.image;
    // Sem foto na matéria: mostra o quadro com a logo Alava (.pic.brand) em vez de esconder a foto.
    // Só some de vez se "Mostrar a foto" estiver desligado no item.
    $('card').classList.toggle('noimg', !SHOW_IMG);
    $('pic').classList.toggle('brand', SHOW_IMG && !it.image);
    $('pic').style.backgroundImage = img ? `url("${{it.image.replace(/"/g, '%22')}}")` : '';
    // Foto que não carrega (site bloqueia ou saiu do ar): cai na logo Alava em vez de um quadro vazio.
    const token = ++picToken;
    if (img) {{ const t = new Image(); t.onerror = () => {{ if (token === picToken) {{ $('pic').style.backgroundImage = ''; $('pic').classList.add('brand'); }} }}; t.src = it.image; }}
    // Selo "PORTAL CONTÁBEIS • TRIBUTÁRIO" quando a matéria tem categoria; senão, a linha de sempre.
    const tag = it.category ? [it.source, it.category].filter(Boolean).join(' • ') : '';
    $('tag').hidden = !tag; $('tag').textContent = tag; $('tag').classList.toggle('pref', !!it.preferred);
    $('meta').textContent = tag ? ago(it.ts) : [it.source, ago(it.ts)].filter(Boolean).join('  ·  ');
    $('headline').textContent = it.title;
    $('summary').textContent = it.summary;
    $('count').textContent = `${{i + 1}} / ${{list.length}}`;
    const bar = $('bar'); bar.style.transition = 'none'; bar.style.width = '0';
    requestAnimationFrame(() => requestAnimationFrame(() => {{ bar.style.transition = `width ${{PER}}ms linear`; bar.style.width = '100%'; }}));
    $('card').classList.remove('out');
  }}, 450);
}}
function restart(target) {{ clearInterval(timer); show(target); timer = setInterval(show, PER); }}
// Botões "Notícia anterior / próxima" do painel: o player chama newsNav(-1) ou newsNav(1) nesta página.
window.newsNav = d => restart(cur + (d < 0 ? -1 : 1));
restart();
// Atualiza a fila a cada 5 min. Na TV, o pacote novo já vem sem as exibidas: recomeça do 1º dele.
setInterval(async () => {{
  try {{
    N = await (await fetch('/api/news/{html.escape(item_id)}' + (TV ? '?tv=1' : ''))).json();
    if (TV) idx = 0;
  }} catch (e) {{}}
}}, 300000);
{NEWS_FX_JS}
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
    UPDATE_LOCK.unlink(missing_ok=True)        # servidor voltou: a atualização (se havia) terminou
    _migrate_news_sources()                    # 0.14.0: itens de notícias antigos ganham as fontes contábeis
    report_prune()                             # 0.17.0: relatório guarda só os últimos REPORT_KEEP_DAYS dias
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
