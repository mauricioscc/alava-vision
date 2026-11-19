"""
Alava Vision — Player (player.py) · versão 0.15.0

Abre o Chrome em tela cheia SEMPRE no monitor da TV (por padrão o 2º monitor) e exibe
o conteúdo que o servidor manda exibir AGORA, respeitando a programação do painel.

COMO RODAR (com o servidor já rodando; porta = PORT do .env, padrão 8080)
    python player.py                          # TV no 2º monitor (padrão)
    python player.py --list-monitors          # mostra a numeração dos monitores e sai
    python player.py --monitor 3              # TV em outro monitor
    python player.py --monitor 1              # testar com uma tela só (ocupa o monitor principal!)
    python player.py --monitor 0 --screen-x 1366 --screen-y -371   # posição manual (modo antigo)
    Monitor padrão também pode ser definido no .env: PLAYER_MONITOR=2
    Fechar: Ctrl+C no terminal (ou Alt+F4 com o foco na TV).

    Servidor + player juntos: iniciar_alava_vision.bat

COMO O PLAYER FICA SABENDO DAS MUDANÇAS (0.8.0)
    • Mantém uma conexão WebSocket aberta em ws://127.0.0.1:PORT/ws/player. O servidor manda o
      estado na hora em que alguém salva no painel ou a programação troca de bloco.
    • Se a conexão cair (servidor reiniciando, servidor antigo sem WebSocket), volta a consultar
      GET /api/player/state a cada 5 s e tenta reconectar sozinho (1 s, 2 s, 4 s… até 30 s).
    • No terminal: "Aviso instantâneo ligado" / "Aviso instantâneo caiu".
    • O que acontece quando chega uma mudança (0.11.0, after_change()):
        - a programação trocou de bloco (outra playlist/item avulso/régua) → recomeça do 1º item;
        - salvaram algo no painel, mas o item na tela não mudou → ele continua, sem interromper;
        - o item na tela foi editado → aparece de novo, já com a mudança, e a sequência segue dali;
        - o item na tela foi removido ou desativado → passa para o próximo.
      Antes da 0.11.0, qualquer salvamento no painel voltava a playlist para o 1º item.

COMPORTAMENTO DO MONITOR
    • Ao abrir, o Chrome é posicionado no monitor escolhido e entra em tela cheia (kiosk).
    • A cada 10 s o player confere: se a janela saiu da TV, ela é recolocada.
    • TV desligada/desconectada (monitor sumiu): a janela é minimizada para não cobrir
      o monitor principal. Quando a TV volta, o player a recoloca automaticamente.
    Detalhes em monitors.py.

LOGO DA ALAVA
    O logo faz parte das telas de clima e notícias (static/weather.html, view_news no server.py).
    Sites, imagens, vídeos e mensagens aparecem sem alteração. Exceção: no trânsito (Waze), o
    player desenha a faixa da Alava por cima do Waze (ver TRÂNSITO abaixo).

TRÂNSITO (WAZE) — 0.14.0
    Dentro de outra página o Waze não mostra o trânsito no Chrome do player: os cookies e o
    reCAPTCHA dele são bloqueados como "de terceiros" (no painel funciona porque o navegador de
    quem edita aceita). Por isso o player abre o Waze DIRETO (endereço de GET /api/traffic) e
    desenha a faixa da Alava — logo, título e relógio — empurrando o mapa para baixo dela
    (TRAFFIC_BAND_JS). O script só age em embed.waze.com.
    Testar: abra o item de trânsito na TV; tem que aparecer o selo do reCAPTCHA no canto e as
    linhas coloridas de trânsito. No terminal do player: "traffic · <nome> — Ns".

COMO REVERTER
    Com Git:  git log --oneline  e  git checkout <commit> -- player.py
    Para a 0.10.0 (antes de after_change):  git checkout 8c60d7f -- player.py
    Sem Git:  backup_v0.2.0_20261117/player.py (versão 0.2.0)

MAPA DO CÓDIGO
    Caminhos dos navegadores ........ BROWSER_PATHS
    Abrir Chrome com porta CDP ...... find_browser(), launch_browser(), cdp_up()
    Monitor da TV ................... target_monitor(), browser_pid(), MonitorGuard  (+ monitors.py)
    Consulta ao servidor ............ fetch_state()  → GET /api/player/state (reserva quando o WebSocket cai)
    Aviso instantâneo (WebSocket) ... PushChannel  → ws://127.0.0.1:PORT/ws/player (thread "push")
    Janela de horário de mensagens .. time_in_window()
    Contador que some após o fim .... countdown_visible()   (config.hide_after)
    Vídeo sem repetição ............. plays_once(), VIDEO_ENDED_JS  → avança quando o vídeo acaba
    Curiosidades ("Hoje é dia") ..... today_count() (pula o item em dia sem nada), today_per_card()
                                      (0.14.0: segundos por card; tempo do item = por card × cards de hoje),
                                      curiosity_due() → intercala /view/today (Configurações)
    Itens que podem ir para a tela .. playable()
    Mudança durante a exibição ...... after_change(), _item_key()  (não recomeça a playlist a cada salvamento)
    Avisos: login e Waze (0.15.0) ... report_alert() → POST /api/player/alert; LOGIN_CHECK_JS (senha/captcha),
                                      on_response() vigia live-map/api/georss; WAZE_WAIT, WAZE_RETRY, BLOCKED_HTML;
                                      set_alert()/clear_alert() e as checagens dentro do laço de exibição do run()
    "Na TV agora" e Pular item ...... report_now() → POST /api/player/now; state["skip"] na signature()
                                      e em after_change() ("next") → encerra o item e vai ao próximo
    URL de cada tipo de item ........ item_url(), traffic_target() (trânsito → Waze direto)
    Faixa da Alava sobre o Waze ..... TRAFFIC_BAND_JS, traffic_band_script()  (registrada no run())
    Loop de exibição ................ run()
    Parâmetros de linha de comando .. main()
"""
import argparse
import base64
import json
import os
import subprocess
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import monitors

__version__ = "0.15.0"

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

IDLE_HTML = """<body style="margin:0;background:#0a0a14;color:#4a5568;font-family:system-ui;
display:flex;align-items:center;justify-content:center;height:100vh;font-size:3vw;text-align:center">
<div>📺<br><span style="font-size:1.8vw;margin-top:16px;display:block">Nenhum item ativo.<br>Acesse o painel para adicionar conteúdo.</span></div></body>"""

BROWSER_PATHS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ],
    "msedge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/usr/bin/microsoft-edge",
    ],
}


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


def fetch_state(server: str) -> dict:
    with urllib.request.urlopen(f"{server}/api/player/state", timeout=5) as r:
        return json.load(r)


def signature(state: dict) -> tuple:
    """O que importa para saber se a TV precisa trocar de conteúdo.
    "skip" (0.12.0) muda quando alguém clica em "Pular item" no painel."""
    return state.get("version"), state.get("slot"), state.get("skip")


class PushChannel:
    """Conexão WebSocket com o servidor, numa thread própria.

    O Playwright só pode ser usado pela thread principal, então esta thread não mexe na tela:
    ela guarda o último estado recebido em `latest` e acende `changed`. O loop de exibição
    confere esses dois a cada segundo.
    """

    def __init__(self, port: int):
        self.url = f"ws://127.0.0.1:{port}/ws/player"
        self.latest: dict | None = None
        self.connected = False
        self.changed = threading.Event()
        threading.Thread(target=self._loop, name="push", daemon=True).start()

    def current(self) -> dict | None:
        """Último estado recebido, ou None se a conexão não está ativa (aí use o HTTP)."""
        latest = self.latest  # lido uma vez só: a thread pode zerá-lo a qualquer momento
        return latest if self.connected else None

    def wait(self, seconds: float) -> bool:
        """Espera até `seconds` ou até chegar um aviso. True = chegou aviso."""
        hit = self.changed.wait(seconds)
        self.changed.clear()
        return hit

    def _loop(self) -> None:
        from websockets.sync.client import connect

        delay, ever_connected, warned = 1, False, False
        while True:
            try:
                with connect(self.url, open_timeout=5) as ws:
                    self.connected, ever_connected, delay = True, True, 1
                    log("Aviso instantâneo ligado (WebSocket conectado)")
                    for msg in ws:
                        self.latest = json.loads(msg)
                        self.changed.set()
            except Exception as e:
                if not ever_connected and not warned:
                    log("Aviso instantâneo indisponível (servidor fora do ar ou de versão antiga), "
                        "consultando a cada 5 s:", str(e).splitlines()[0])
                    warned = True
            if self.connected:
                log("Aviso instantâneo caiu — consultando a cada 5 s até reconectar")
            self.connected, self.latest = False, None
            time.sleep(delay)
            delay = min(delay * 2, 30)


def cdp_up(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1)
        return True
    except Exception:
        return False


def find_browser(args) -> str:
    if args.browser_path:
        return args.browser_path
    for path in BROWSER_PATHS.get(args.channel or "chrome", []):
        if os.path.exists(path):
            return path
    raise RuntimeError("Chrome não encontrado. Use --browser-path ou --channel msedge.")


def target_monitor(args) -> dict | None:
    """Monitor da TV (None em modo manual, fora do Windows ou se ele não estiver conectado)."""
    if args.monitor <= 0 or not monitors.IS_WINDOWS:
        return None
    return monitors.pick_monitor(args.monitor)


def launch_browser(args) -> subprocess.Popen | None:
    if cdp_up(args.cdp_port):
        log("Reaproveitando navegador já aberto na porta", args.cdp_port)
        return None
    exe = find_browser(args)
    # Abre já sobre o monitor da TV; o modo kiosk ocupa a tela em que a janela nasce.
    # Se a posição não bater (escala de DPI, TV desligada), o MonitorGuard corrige em seguida.
    mon = target_monitor(args)
    x, y, w, h = ((mon["left"], mon["top"], mon["width"], mon["height"]) if mon
                  else (args.screen_x, args.screen_y, args.width, args.height))
    cmd = [
        exe,
        f"--remote-debugging-port={args.cdp_port}",
        f"--user-data-dir={Path(args.profile).resolve()}",
        "--kiosk",
        f"--window-position={x},{y}",
        f"--window-size={w},{h}",
        "--no-first-run", "--no-default-browser-check", "--noerrdialogs",
        "--disable-infobars", "--disable-session-crashed-bubble",
        "--disable-features=Translate",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-blink-features=AutomationControlled",
        "about:blank",
    ]
    log("Abrindo", exe)
    proc = subprocess.Popen(cmd)
    for _ in range(60):
        if cdp_up(args.cdp_port):
            return proc
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("Navegador abriu mas a porta CDP não respondeu.")


def time_in_window(config: dict) -> bool:
    """Mensagens podem ter janela própria (ex.: 12:00–14:00) além da timeline."""
    start, end = config.get("time_start", ""), config.get("time_end", "")
    if not start or not end:
        return True
    return start <= datetime.now().strftime("%H:%M") <= end


def countdown_visible(item: dict) -> bool:
    """Contador com "sumir depois do fim" ligado deixa de ser exibido quando a hora chega."""
    cfg = item.get("config", {})
    if item.get("type") != "countdown" or not cfg.get("hide_after"):
        return True
    try:
        return datetime.now() < datetime.fromisoformat(cfg.get("target", ""))
    except ValueError:
        return True   # data inválida: mostra o item (a própria tela avisa sem números)


def plays_once(item: dict) -> bool:
    """Vídeo com "Repetir" desligado: toca uma vez e o player avança quando ele acaba."""
    return item.get("type") == "video" and item.get("config", {}).get("loop", True) is False


VIDEO_ENDED_JS = "() => { const v = document.querySelector('video'); return !!(v && v.ended); }"


def today_count(state: dict) -> int:
    return int((state.get("today") or {}).get("count") or 0)


def curiosity_due(state: dict, last_shown: float) -> dict | None:
    """Curiosidades automáticas (Configurações → Curiosidades e datas).

    Devolve um item "today" para intercalar AGORA, ou None. Regras: opção ligada, há algo
    para hoje, dentro do horário de serviço, já passou o intervalo desde a última vez e a
    TV não está num item avulso agendado (que, pela regra da grade, ocupa a tela sozinho).
    """
    auto = (state.get("today") or {}).get("auto") or {}
    if not auto.get("enabled") or today_count(state) == 0:
        return None
    if (state.get("source") or {}).get("kind") == "item":
        return None
    now = datetime.now().strftime("%H:%M")
    if not (auto.get("start", "08:00") <= now < auto.get("end", "18:00")):
        return None
    if time.time() - last_shown < int(auto.get("every_min", 30)) * 60:
        return None
    return {"id": "auto", "type": "today", "name": "Curiosidade do dia", "active": 1,
            "duration": int(auto.get("duration", 15)), "config": {}}


TODAY_SECONDS_PER_CARD = 30   # igual ao do server.py; vale quando o item/servidor não informa


def today_per_card(item: dict, state: dict) -> int:
    """Segundos de cada card do "Hoje é dia" (0.14.0): do item (config.per_card) ou, na curiosidade
    automática, das Configurações (state.today.auto.per_card)."""
    if item.get("id") == "auto":
        raw = ((state.get("today") or {}).get("auto") or {}).get("per_card")
    else:
        raw = (item.get("config") or {}).get("per_card")
    try:
        return max(5, min(120, int(raw)))
    except (TypeError, ValueError):
        return TODAY_SECONDS_PER_CARD


def playable(state: dict) -> list[dict]:
    """Itens da rotação atual que podem ir para a tela agora."""
    return [x for x in state.get("items", [])
            if x.get("active") and time_in_window(x.get("config", {})) and countdown_visible(x)
            and (x.get("type") != "today" or today_count(state) > 0)]


def _item_key(item: dict) -> str:
    """O que muda a tela de um item (nome e ordem não contam)."""
    return json.dumps([item.get("type"), item.get("config"), item.get("duration")], sort_keys=True)


def after_change(item: dict, old: dict, new: dict) -> tuple[str, int | None]:
    """O que fazer com o item que está na tela quando chega um estado novo (0.11.0).

    Antes, qualquer salvamento no painel voltava a playlist para o 1º item, e quem estava
    configurando o painel via o primeiro item (ex.: Notícias) recomeçar várias vezes.
    Agora só uma troca de bloco da programação (slot) recomeça do início:
      "restart", 0     → outro bloco/régua entrou no ar: começa a playlist nova do início;
      "keep",  idx     → o item na tela não mudou: continua sem interromper; idx = próximo da fila;
      "reload", idx    → o item na tela foi editado: mostra de novo já com a mudança (idx = ele);
      "skip",  idx     → foi removido/desativado: vai para o próximo que ainda existe;
      "next",  None    → clicaram em "Pular item" no painel: encerra este e vai para o próximo.
    idx None = manter o índice atual.
    """
    if new.get("slot") != old.get("slot"):
        return "restart", 0
    if new.get("skip") != old.get("skip"):           # botão "Pular item" do painel (0.12.0)
        return "next", None                          # idx já aponta para o próximo da fila
    if item.get("id") == "auto":                     # curiosidade intercalada: não está na lista
        return "keep", None
    new_items, old_items = playable(new), playable(old)
    new_ids = [x["id"] for x in new_items]
    if item["id"] in new_ids:
        pos = new_ids.index(item["id"])
        if _item_key(new_items[pos]) == _item_key(item):
            return "keep", pos + 1
        return "reload", pos
    old_ids = [x["id"] for x in old_items]
    after = old_ids[old_ids.index(item["id"]) + 1:] if item["id"] in old_ids else []
    nxt = next((new_ids.index(i) for i in after if i in new_ids), 0)
    return "skip", nxt


def report_now(server: str, item: dict, duration: int, source: str, nxt: str | None, skip_seq) -> None:
    """Conta ao servidor o que entrou na tela, para o painel mostrar "Na TV agora" (0.12.0).
    Numa thread à parte e sem esperar: se o servidor não responder, a TV segue normalmente."""
    body = json.dumps({"id": item.get("id"), "name": item.get("name"), "type": item.get("type"),
                       "duration": duration, "source": source, "next": nxt, "skip_seq": skip_seq}).encode()

    def send():
        try:
            rq = urllib.request.Request(f"{server}/api/player/now", data=body, method="POST",
                                        headers={"Content-Type": "application/json"})
            urllib.request.urlopen(rq, timeout=3).close()
        except Exception:
            pass   # servidor antigo (sem a rota) ou reiniciando

    threading.Thread(target=send, name="agora", daemon=True).start()


# ─── Avisos para o painel: site no login e Waze fora (0.15.0) ─────────────────
#
# Quando um item não pode ir ao ar, o player PULA o item e avisa o painel (POST /api/player/alert).
# O painel mostra uma faixa de aviso com o que fazer. Quando o item volta a funcionar, o aviso some sozinho.
#   • login — site (ex.: Acessórias) abriu na tela de login: campo de senha visível, ou captcha num
#     endereço de login. Conferido 5 s depois de abrir e a cada 30 s. Desliga por item: config.login_watch.
#   • waze  — o Waze não abriu, ou a chamada que traz o trânsito (live-map/api/georss) falhou ou não veio em
#     WAZE_WAIT s. Depois de uma falha, só tenta de novo após WAZE_RETRY s (para não insistir no reCAPTCHA).
# Se o item bloqueado for o ÚNICO da playlist, mostra BLOCKED_HTML no lugar (em vez de girar sem parar).
WAZE_WAIT = 20
WAZE_RETRY = 300
LOGIN_FIRST_CHECK = 5
LOGIN_EVERY = 30

LOGIN_CHECK_JS = """() => {
  const vis = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 2 && r.height > 2 && s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0'; };
  const pw = [...document.querySelectorAll('input[type=password]')].some(vis);
  const cap = [...document.querySelectorAll('iframe[src*="recaptcha/api2/anchor"], iframe[src*="recaptcha/enterprise/anchor"], ' +
    'iframe[src*="hcaptcha"], iframe[src*="turnstile"], .g-recaptcha, .h-captcha, .cf-turnstile')].some(vis);
  const path = (location.pathname + location.hash).toLowerCase();
  const loginUrl = /(^|[\\/#?_-])(login|signin|sign-in|entrar|auth|acesso)([\\/?#._-]|$)/.test(path);
  return {login: pw || (loginUrl && cap), captcha: cap, url: location.href};
}"""

BLOCKED_HTML = """<body style="margin:0;background:#0b1120;color:#e2e8f0;font-family:'Segoe UI',system-ui,sans-serif;
height:100vh;display:flex;align-items:center;justify-content:center;text-align:center">
<div><div style="font-size:10vh">__ICON__</div><div style="font-size:5vh;font-weight:700;margin:2vh 0 1.5vh">__TITLE__</div>
<div style="font-size:2.8vh;opacity:.7;max-width:70vw">__TEXT__</div></div></body>"""


def waze_verdict(net: dict, nav_t: float, now: float) -> tuple[bool | None, str]:
    """Depois de abrir o Waze em nav_t: (True, …) trânsito chegou; (False, motivo) falhou; (None, "") ainda esperando.
    net = última resposta vista de live-map/api/georss: {"status": código HTTP, "at": quando}."""
    if net.get("at", 0) >= nav_t:
        return net.get("status") == 200, f"HTTP {net.get('status')}"
    if now - nav_t >= WAZE_WAIT:
        return False, f"sem resposta em {WAZE_WAIT} s"
    return None, ""


def blocked_html(icon: str, title: str, text: str) -> str:
    import html as _h
    return (BLOCKED_HTML.replace("__ICON__", icon).replace("__TITLE__", _h.escape(title))
            .replace("__TEXT__", _h.escape(text)))


def show_html(page, content: str) -> None:
    """Mostra um HTML fixo (aviso, "nenhum item"). Passa antes por about:blank: o set_content sozinho reaproveita
    a janela, e os timers da tela anterior (ex.: troca de manchetes) continuariam rodando por cima do aviso."""
    try:
        page.goto("about:blank")
    except Exception:
        pass
    page.set_content(content)


def report_alert(server: str, key: str, kind: str, active: bool, item: dict | None = None,
                 url: str = "", detail: str = "") -> None:
    """Avisa (ou limpa o aviso) no painel. Em thread à parte: se o servidor não responder, segue."""
    body = json.dumps({"key": key, "kind": kind, "active": active, "item_id": (item or {}).get("id"),
                       "item_name": (item or {}).get("name"), "url": url, "detail": detail}).encode()

    def send():
        try:
            rq = urllib.request.Request(f"{server}/api/player/alert", data=body, method="POST",
                                        headers={"Content-Type": "application/json"})
            urllib.request.urlopen(rq, timeout=3).close()
        except Exception:
            pass   # servidor antigo (sem a rota) ou reiniciando

    threading.Thread(target=send, name="aviso", daemon=True).start()


def item_url(item: dict, server: str) -> str:
    t = item["type"]
    if t == "url":
        return item["config"].get("url", "about:blank")
    if t in ("weather", "traffic", "today"):
        return f"{server}/view/{t}"
    return f"{server}/view/{t}/{item['id']}"


# ─── Trânsito: Waze aberto direto (0.14.0, portado da 0.7.0) ──────────────────
#
# Dentro da nossa página (iframe) o Waze não mostra o trânsito no Chrome do player: o cookie e o
# reCAPTCHA dele são bloqueados como "de terceiros", e o mapa aparece sem as linhas coloridas.
# Por isso o player abre o Waze DIRETO (endereço de GET /api/traffic) e desenha por cima a faixa
# da Alava — logo, título e relógio —, empurrando o mapa para baixo dela.

def traffic_target(server: str) -> tuple[str, str | None]:
    """(endereço a abrir, título da faixa). Título None = usar a nossa tela /view/traffic."""
    try:
        with urllib.request.urlopen(f"{server}/api/traffic", timeout=5) as r:
            t = json.load(r)
    except Exception:
        return f"{server}/view/traffic", None
    return (t["url"], t["title"]) if t.get("direct") else (f"{server}/view/traffic", None)


# Registrada com add_init_script: roda no início de cada página, mas só faz algo em embed.waze.com.
# Faixa fixa de 9% da altura (mesmo visual de /view/traffic); o <body> do Waze desce para logo abaixo
# dela e o mapa recalcula o tamanho com o evento "resize". Estilos via element.style (funciona mesmo
# com CSP restritiva) e logo embutido como data: (a página é https; imagem de http://127.0.0.1 seria
# bloqueada). Se o título mudar (cidade nova), um novo script é registrado e o último vale.
TRAFFIC_BAND_JS = """
(() => {
  if (location.hostname !== 'embed.waze.com' || window.top !== window) return;
  const LOGO = __LOGO__, TITLE = __TITLE__;
  const css = (el, props) => Object.entries(props).forEach(([k, v]) =>
    el.style.setProperty(k.replace(/[A-Z]/g, m => '-' + m.toLowerCase()), v, 'important'));
  const apply = () => {
    const de = document.documentElement, b = document.body;
    if (!de) return;
    css(de, {background: '#0b1220'});
    if (b && b.dataset.alavaBand !== '1') {
      css(b, {position: 'fixed', top: '9vh', left: '0', right: '0', bottom: '0', height: 'auto',
              width: 'auto', margin: '0', overflow: 'hidden', transform: 'translateZ(0)'});
      b.dataset.alavaBand = '1';
      window.dispatchEvent(new Event('resize'));
    }
    let band = document.getElementById('alava-band');
    if (!band) {
      band = document.createElement('div');
      band.id = 'alava-band';
      css(band, {position: 'fixed', top: '0', left: '0', right: '0', height: '9vh', zIndex: '2147483647',
                 background: '#0b1220', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                 padding: '0 1.8vw', boxSizing: 'border-box', color: '#fff', fontFamily: 'system-ui, Segoe UI, sans-serif'});
      const img = document.createElement('img');
      img.src = LOGO; img.alt = 'Alava';
      css(img, {height: 'clamp(26px, 4.2vh, 72px)', width: 'auto', opacity: '.9'});
      const right = document.createElement('div');
      css(right, {display: 'flex', alignItems: 'baseline', gap: '2vw'});
      const title = document.createElement('span');
      title.id = 'alava-band-title';
      css(title, {fontSize: '2.2vh', fontWeight: '600', letterSpacing: '.2em', textTransform: 'uppercase', opacity: '.85'});
      const clock = document.createElement('span');
      clock.id = 'alava-band-clock';
      css(clock, {fontSize: '3.6vh', fontWeight: '300', fontVariantNumeric: 'tabular-nums'});
      right.append(title, clock);
      band.append(img, right);
      de.appendChild(band);
    }
    document.getElementById('alava-band-title').textContent = TITLE;
    const n = new Date();
    document.getElementById('alava-band-clock').textContent =
      String(n.getHours()).padStart(2, '0') + ':' + String(n.getMinutes()).padStart(2, '0');
  };
  apply();
  document.addEventListener('DOMContentLoaded', apply);
  setInterval(apply, 1000);
})();
"""


def traffic_band_script(title: str) -> str:
    logo = BASE / "assets" / "watermark.png"
    src = "data:image/png;base64," + base64.b64encode(logo.read_bytes()).decode() if logo.exists() else ""
    return TRAFFIC_BAND_JS.replace("__LOGO__", json.dumps(src)).replace("__TITLE__", json.dumps(title))


# ─── Monitor da TV ────────────────────────────────────────────────────────────

def browser_pid(browser, proc: subprocess.Popen | None) -> int | None:
    """PID do processo principal do Chrome (dono da janela), pedido ao próprio Chrome."""
    try:
        info = browser.new_browser_cdp_session().send("SystemInfo.getProcessInfo")
        return next(p["id"] for p in info["processInfo"] if p["type"] == "browser")
    except Exception:
        return proc.pid if proc else None


class MonitorGuard:
    """Confere de tempos em tempos se a janela do player está no monitor da TV."""

    def __init__(self, args, pid: int | None):
        self.number, self.pid = args.monitor, pid
        self.enabled = args.monitor > 0 and monitors.IS_WINDOWS and pid is not None
        self.last_status, self.last_check = None, 0.0

    def check(self, force: bool = False) -> None:
        if not self.enabled or (not force and time.time() - self.last_check < 10):
            return
        self.last_check = time.time()
        status = monitors.ensure_on_monitor(self.pid, self.number)
        if status != self.last_status or status == "moved":
            mon = monitors.pick_monitor(self.number)
            if status == "ok":
                log("Player no", monitors.describe(mon))
            elif status == "moved":
                log("Janela posicionada no", monitors.describe(mon))
            elif status == "no-monitor":
                log(f"Monitor {self.number} não encontrado (TV desligada ou desconectada?). "
                    "Player minimizado, aguardando a TV voltar.")
        self.last_status = status

    def wait_window(self, timeout: float = 15) -> None:
        """Logo após abrir o Chrome a janela demora um pouco para existir."""
        end = time.time() + timeout
        while self.enabled and time.time() < end:
            self.check(force=True)
            if self.last_status not in (None, "no-window"):
                time.sleep(1.5)
                self.check(force=True)  # o kiosk às vezes se reposiciona ao terminar de abrir
                return
            time.sleep(0.5)
        if self.enabled:
            log("Não encontrei a janela do Chrome para posicionar no monitor", self.number)


# ─── Loop de exibição ─────────────────────────────────────────────────────────

def run(args, push: PushChannel):
    from playwright.sync_api import sync_playwright

    server = f"http://127.0.0.1:{args.port}"

    proc = None
    with sync_playwright() as p:
        try:
            proc = launch_browser(args)
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{args.cdp_port}")
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.on("dialog", lambda d: d.dismiss())
            # Waze: guarda a resposta da chamada que traz o trânsito (0.15.0, aviso "Waze fora")
            waze_net = {"status": None, "at": 0.0}

            def on_response(r):
                if "/live-map/api/georss" in r.url:
                    waze_net["status"], waze_net["at"] = r.status, time.time()
            page.on("response", on_response)
            alerts_on: set[str] = set()      # avisos que ESTE player levantou (para limpar na volta)
            checked_ok: set[str] = set()     # já confirmou OK desde que abriu (limpa aviso antigo do servidor)
            waze_fail_at = 0.0

            def set_alert(key, kind, item, url, detail):
                if key not in alerts_on:
                    log(f"AVISO: {item.get('name')} — {detail}. Pulando o item até voltar a funcionar.")
                alerts_on.add(key)
                checked_ok.discard(key)
                report_alert(server, key, kind, True, item, url, detail)

            def clear_alert(key, kind):
                if key in alerts_on or key not in checked_ok:
                    report_alert(server, key, kind, False)
                    if key in alerts_on:
                        log(f"Aviso resolvido: {key}")
                alerts_on.discard(key)
                checked_ok.add(key)

            guard = MonitorGuard(args, browser_pid(browser, proc))
            guard.wait_window()

            state: dict = {"items": []}
            idx = 0
            current_url = None
            registered_band = None   # título da faixa do Waze já registrada (traffic_band_script)
            last_curiosity = 0.0   # 0 = a primeira curiosidade automática pode aparecer logo

            while True:
                pushed = push.current()
                if pushed:
                    state = pushed               # já veio pelo WebSocket, sem perguntar
                else:
                    try:
                        state = fetch_state(server)
                    except Exception as e:
                        log("Sem API, usando última programação:", e)

                items = playable(state)

                if not items:
                    show_html(page, IDLE_HTML)
                    current_url = None
                    idx = 0
                    for _ in range(5):
                        hit = push.wait(1)       # conteúdo novo no painel aparece na hora
                        guard.check()
                        if hit:
                            break
                    continue

                idx %= len(items)
                extra = curiosity_due(state, last_curiosity)
                if extra:                        # intercala sem avançar a playlist
                    item, last_curiosity = extra, time.time()
                else:
                    item = items[idx]
                    idx += 1
                duration = max(3, int(item.get("duration", 30)))
                if item["type"] == "today":              # 0.14.0: cada card fica "per" s; o item, per × cards de hoje
                    per = today_per_card(item, state)
                    duration = per * max(1, today_count(state))
                    url = f"{server}/view/today?per={per}"
                elif item["type"] == "traffic":          # Waze direto + faixa da Alava (ver traffic_target)
                    url, band_title = traffic_target(server)
                    if band_title and band_title != registered_band:
                        page.add_init_script(traffic_band_script(band_title))
                        registered_band = band_title
                else:
                    url = item_url(item, server)
                src = state.get("source") or {}
                log(f"[{src.get('name', '?')}] {item['type']} · {item['name']} — {duration}s")

                # Avisos (0.15.0): Waze fora / site pedindo login → pula o item e avisa o painel
                is_waze = item["type"] == "traffic" and url.startswith("https://embed.waze.com")
                watch_login = item["type"] == "url" and (item.get("config") or {}).get("login_watch", True)
                login_key = f"login:{item.get('id')}"
                alone = len(items) == 1 and not extra       # único item: mostra o aviso na tela em vez de girar
                blocked = None
                if is_waze and "waze" in alerts_on and time.time() - waze_fail_at < WAZE_RETRY:
                    if not alone:
                        time.sleep(.2)
                        continue                            # Waze falhou há pouco: não insiste (reCAPTCHA)
                    blocked = ("🚗", "Trânsito indisponível no momento",
                               "O Waze não está entregando o trânsito. A TV tenta de novo em alguns minutos.")

                # Um único item (ex.: sobreposição de clima) não é recarregado a cada ciclo.
                # Exceção: vídeo sem repetição precisa recomeçar do início a cada volta.
                once = plays_once(item)
                reloaded = False
                if blocked:
                    show_html(page, blocked_html(*blocked))
                    current_url = None
                elif once or not (len(items) == 1 and url == current_url):
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=20_000)
                        current_url, reloaded = url, True
                    except Exception as e:
                        if "closed" in str(e).lower():
                            raise
                        log("Falha ao navegar, pulando:", str(e).splitlines()[0])
                        current_url = None
                        if is_waze:
                            waze_fail_at = time.time()
                            set_alert("waze", "waze", item, url, "o Waze não abriu (" + str(e).splitlines()[0][:90] + ")")
                        time.sleep(2)
                        continue
                nav_t = time.time()
                waze_pending = is_waze and reloaded         # espera a chamada do trânsito desta carga
                next_login = nav_t + LOGIN_FIRST_CHECK if watch_login and not blocked else None

                # Painel "Na TV agora": este item e o próximo da fila
                nxt = items[idx % len(items)]["name"] if len(items) > 1 or extra else None
                report_now(server, item, duration, src.get("name", ""), nxt, state.get("skip"))

                # Durante a exibição, confere se algo mudou: versão (alguém salvou no painel)
                # ou slot (a grade mudou de bloco). Com o WebSocket ligado, o aviso chega na
                # hora; sem ele, pergunta ao servidor a cada 5 s.
                shown = signature(state)
                deadline = time.time() + duration
                last_check = time.time()
                while time.time() < deadline:
                    push.wait(1)
                    guard.check()
                    # Waze: a chamada do trânsito veio com sucesso? (ou passou WAZE_WAIT sem vir)
                    verdict, why = waze_verdict(waze_net, nav_t, time.time()) if waze_pending else (None, "")
                    if verdict is not None:
                        waze_pending = False
                        if verdict:
                            clear_alert("waze", "waze")
                        else:
                            waze_fail_at = time.time()
                            set_alert("waze", "waze", item, url, f"o Waze não entregou o trânsito ({why})")
                            current_url = None
                            if not alone:
                                break
                            show_html(page, blocked_html("🚗", "Trânsito indisponível no momento",
                                                          "O Waze não está entregando o trânsito. A TV tenta de novo em alguns minutos."))
                    # Site: abriu na tela de login? (5 s depois de abrir e a cada 30 s)
                    if next_login and time.time() >= next_login:
                        next_login = time.time() + LOGIN_EVERY
                        try:
                            res = page.evaluate(LOGIN_CHECK_JS)
                        except Exception:
                            res = None
                        if res and res.get("login"):
                            set_alert(login_key, "login", item, res.get("url") or url,
                                      "abriu na tela de login" + (" com captcha" if res.get("captcha") else ""))
                            current_url = None
                            if not alone:
                                break
                            show_html(page, blocked_html("🔒", f"{item.get('name', 'O site')} pediu login",
                                                          "Faça o login no computador da TV (o passo a passo está no aviso do painel)."))
                            next_login, deadline = None, min(deadline, time.time() + 60)   # tenta de novo em 1 min
                        elif res:
                            clear_alert(login_key, "login")
                    if once:
                        try:
                            if page.evaluate(VIDEO_ENDED_JS):
                                log("Vídeo terminou — próximo item")
                                break
                        except Exception:
                            pass  # página trocando ou fechada: segue pelo tempo normal
                    fresh = push.current()
                    if not fresh:
                        if time.time() - last_check < 5:
                            continue
                        last_check = time.time()
                        try:
                            fresh = fetch_state(server)
                        except Exception:
                            continue
                    if signature(fresh) != shown:
                        action, new_idx = after_change(item, state, fresh)
                        state, shown = fresh, signature(fresh)
                        if new_idx is not None:
                            idx = new_idx
                        if action == "keep":
                            continue                     # salvaram outra coisa: segue exibindo este item
                        log({"restart": "Programação mudou — trocando conteúdo",
                             "reload": "Item editado no painel — mostrando de novo",
                             "skip": "Item removido/desativado — próximo",
                             "next": "Pulado pelo painel — próximo item"}[action])
                        current_url = None
                        deadline = 0
        finally:
            if proc:
                try:
                    proc.terminate()
                except Exception:
                    pass


def main():
    ap = argparse.ArgumentParser(description=f"Alava Vision Player {__version__}")
    ap.add_argument("--monitor", type=int, default=int(os.getenv("PLAYER_MONITOR", "2")),
                    help="monitor da TV: 1 = principal, 2 = segundo (padrão), 0 = posição manual")
    ap.add_argument("--list-monitors", action="store_true", help="lista os monitores e sai")
    ap.add_argument("--screen-x", type=int, default=0, help="só com --monitor 0: posição X da janela")
    ap.add_argument("--screen-y", type=int, default=0, help="só com --monitor 0: posição Y da janela")
    ap.add_argument("--width", type=int, default=1920, help="só com --monitor 0")
    ap.add_argument("--height", type=int, default=1080, help="só com --monitor 0")
    ap.add_argument("--port", type=int, default=int(os.getenv("PORT", "8080")),
                    help="porta do servidor Alava Vision (padrão: PORT do .env ou 8080)")
    ap.add_argument("--channel", default="chrome", help="chrome | msedge")
    ap.add_argument("--browser-path", default="")
    ap.add_argument("--cdp-port", type=int, default=9222)
    ap.add_argument("--profile", default="data/browser-profile")
    args = ap.parse_args()

    if args.list_monitors:
        for m in monitors.list_monitors() or []:
            print(monitors.describe(m))
        return

    mon = target_monitor(args)
    if args.monitor > 0 and monitors.IS_WINDOWS:
        log(f"Alava Vision Player {__version__} — alvo:",
            monitors.describe(mon) if mon else f"monitor {args.monitor} (não conectado agora)")

    push = PushChannel(args.port)  # uma só conexão, mesmo se o player reiniciar
    while True:
        try:
            run(args, push)
        except KeyboardInterrupt:
            log("Player encerrado.")
            break
        except Exception as e:
            log("Player caiu, reiniciando em 5s:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
