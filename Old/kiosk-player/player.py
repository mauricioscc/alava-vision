"""Kiosk Player: abre o Chrome em tela cheia e rotaciona as páginas do painel.

Uso:
    python player.py --api http://localhost:8080/api/pages --screen-x 1920

--screen-x  = posição horizontal da TV (largura do monitor principal).
              Se a TV é a tela estendida à direita de um monitor 1920px, use 1920.
              Se o servidor só tem a TV, use 0.

Modos (--mode):
    cdp         (padrão) abre o Chrome/Edge como programa normal e só se conecta
                a ele para trocar de página. Evita as flags de automação, então
                captchas e logins costumam funcionar.
    playwright  lança o navegador pelo Playwright (modo anterior).
"""
import argparse
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

IDLE_HTML = """
<body style="margin:0;background:#0f1115;color:#8b93a5;font-family:system-ui;
display:flex;align-items:center;justify-content:center;height:100vh;font-size:3vw;text-align:center">
<div>📺<br>Nenhuma página ativa.<br><span style="font-size:1.6vw">Cadastre no painel ADM.</span></div></body>
"""

BROWSER_PATHS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ],
    "msedge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/usr/bin/microsoft-edge",
    ],
}


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


def fetch(api):
    with urllib.request.urlopen(api, timeout=5) as r:
        return json.load(r)


def cdp_up(port):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1)
        return True
    except Exception:
        return False


def find_browser(args):
    if args.browser_path:
        return args.browser_path
    for path in BROWSER_PATHS.get(args.channel or "chrome", []):
        if os.path.exists(path):
            return path
    raise RuntimeError(
        "Chrome não encontrado. Use --browser-path \"C:\\caminho\\chrome.exe\" "
        "ou --channel msedge."
    )


def launch_native(args):
    """Abre o navegador como programa normal, só com a porta de depuração ligada."""
    if cdp_up(args.cdp_port):
        log("Reaproveitando navegador já aberto na porta", args.cdp_port)
        return None
    exe = find_browser(args)
    profile = str(Path(args.profile).resolve())
    cmd = [
        exe,
        f"--remote-debugging-port={args.cdp_port}",
        f"--user-data-dir={profile}",
        "--kiosk",
        f"--window-position={args.screen_x},{args.screen_y}",
        f"--window-size={args.width},{args.height}",
        "--no-first-run",
        "--no-default-browser-check",
        "--noerrdialogs",
        "--disable-infobars",
        "--disable-session-crashed-bubble",
        "--disable-features=Translate",
        "--autoplay-policy=no-user-gesture-required",
        "about:blank",
    ]
    log("Abrindo", exe)
    proc = subprocess.Popen(cmd)
    for _ in range(60):
        if cdp_up(args.cdp_port):
            return proc
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("O navegador abriu mas a porta de controle não respondeu.")


def open_context(p, args):
    """Devolve (ctx, proc). proc é o processo do navegador no modo cdp."""
    if args.mode == "playwright":
        ctx = p.chromium.launch_persistent_context(
            args.profile,
            channel=args.channel or None,
            no_viewport=True,
            headless=False,
            ignore_default_args=["--enable-automation"],
            args=[
                "--kiosk",
                f"--window-position={args.screen_x},{args.screen_y}",
                f"--window-size={args.width},{args.height}",
                "--noerrdialogs",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-session-crashed-bubble",
                "--disable-features=Translate",
                "--autoplay-policy=no-user-gesture-required",
            ],
        )
        return ctx, None

    proc = launch_native(args)
    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{args.cdp_port}")
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    return ctx, proc


def run_once(args):
    proc = None
    with sync_playwright() as p:
        try:
            ctx, proc = open_context(p, args)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.on("dialog", lambda d: d.dismiss())

            cfg = {"version": None, "pages": []}
            idx = 0

            while True:
                try:
                    cfg = fetch(args.api)
                except Exception as e:
                    log("Sem acesso à API, usando última config:", e)

                items = [x for x in cfg.get("pages", []) if x.get("enabled", True) and x.get("url")]
                if not items:
                    page.set_content(IDLE_HTML)
                    time.sleep(5)
                    continue

                idx %= len(items)
                item = items[idx]
                idx += 1
                seconds = max(3, int(item.get("seconds", 30)))
                log(f"Abrindo ({seconds}s): {item['url']}")

                try:
                    page.goto(item["url"], wait_until="domcontentloaded", timeout=20000)
                except Exception as e:
                    if "closed" in str(e).lower():
                        raise
                    log("Falha ao abrir, pulando:", str(e).splitlines()[0])
                    time.sleep(3)
                    continue

                version = cfg.get("version")
                deadline = time.time() + seconds
                last_check = time.time()
                while time.time() < deadline:
                    time.sleep(1)
                    if time.time() - last_check >= 5:
                        last_check = time.time()
                        try:
                            if fetch(args.api).get("version") != version:
                                log("Config alterada, recarregando lista")
                                idx = 0
                                deadline = 0
                        except Exception:
                            pass
        finally:
            if proc is not None:
                try:
                    proc.terminate()
                except Exception:
                    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8080/api/pages")
    ap.add_argument("--screen-x", type=int, default=0, help="posição X da tela da TV")
    ap.add_argument("--screen-y", type=int, default=0)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--mode", choices=["cdp", "playwright"], default="cdp")
    ap.add_argument("--channel", default="chrome",
                    help='"chrome" (padrão), "msedge", ou "" para o Chromium do Playwright (só modo playwright)')
    ap.add_argument("--browser-path", default="", help="caminho completo do .exe, se não for achado sozinho")
    ap.add_argument("--cdp-port", type=int, default=9222)
    ap.add_argument("--profile", default="perfil", help="pasta do perfil (guarda login e cookies)")
    args = ap.parse_args()

    while True:  # se o navegador fechar/crashar, reabre
        try:
            run_once(args)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log("Player caiu, reiniciando em 5s:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
