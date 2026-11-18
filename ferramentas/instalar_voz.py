"""
Alava Vision — Instalador da voz (ferramentas/instalar_voz.py) · versão 0.10.0

Baixa o Piper (leitura em voz alta, open source, roda offline) e uma voz em português do Brasil
para ferramentas/piper/. Depois de instalado, não precisa mais de internet para falar.

COMO RODAR
    python ferramentas/instalar_voz.py              # Piper + voz padrão (faber)
    python ferramentas/instalar_voz.py --voz cadu   # outra voz: faber, cadu ou jeff
    python ferramentas/instalar_voz.py --verificar  # só diz o que já está instalado (sai com 0 se está pronto)
    Também roda pelo painel: Configurações → Voz → "Instalar voz", e pelo instalar.bat.

    Tamanho: Piper ~22 MB + ~63 MB por voz. Pode rodar de novo: o que já existe não é baixado outra vez.

COMO REVERTER
    Apague a pasta ferramentas/piper/. As mensagens com "Ler em voz alta" continuam aparecendo,
    só que sem som.

MAPA DO CÓDIGO
    Endereços de download ...... PIPER_ZIP, VOICES
    Onde instala ............... PIPER_DIR (piper.exe), VOICES_DIR (*.onnx + *.onnx.json)
    Baixar com progresso ....... download()
    Instalar / verificar ....... install(), status()
"""
import argparse
import io
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PIPER_DIR = BASE / "ferramentas" / "piper"
VOICES_DIR = PIPER_DIR / "vozes"
PIPER_EXE = PIPER_DIR / "piper.exe"

# Última versão do Piper com executável pronto para Windows (projeto rhasspy/piper).
PIPER_ZIP = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
# Vozes fixadas na tag v1.0.0: as de "main" foram retreinadas em 11/2026 para o Piper 1.5, que não
# tem executável para Windows, e o piper.exe de 2023 recusa esses arquivos novos com o erro
# '"aɪ" is not a single codepoint'. Fixar a tag também garante que o download é sempre o mesmo.
_HF = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/pt/pt_BR"
VOICES = {   # vozes pt-BR de qualidade "medium" (testadas em 18/11/2026)
    "faber": f"{_HF}/faber/medium/pt_BR-faber-medium.onnx",
    "cadu": f"{_HF}/cadu/medium/pt_BR-cadu-medium.onnx",
    "jeff": f"{_HF}/jeff/medium/pt_BR-jeff-medium.onnx",
}


def log(*a):
    print(*a, flush=True)


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "AlavaVision/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("Content-Length") or 0)
        buf, done, last = io.BytesIO(), 0, -10
        while chunk := r.read(256 * 1024):
            buf.write(chunk)
            done += len(chunk)
            pct = int(done * 100 / total) if total else 0
            if pct >= last + 10:
                log(f"   {pct:3d}%  ({done // (1024 * 1024)} de {total // (1024 * 1024)} MB)")
                last = pct
    return buf.getvalue()


def voice_file(name: str) -> Path:
    return VOICES_DIR / VOICES[name].rsplit("/", 1)[1]


def status() -> dict:
    return {"piper": PIPER_EXE.exists(),
            "voices": [n for n in VOICES if voice_file(n).exists() and voice_file(n).with_suffix(".onnx.json").exists()]}


def install(voice: str = "faber") -> dict:
    if sys.platform != "win32":
        raise SystemExit("Este instalador baixa o Piper para Windows. Em outro sistema, instale o Piper manualmente.")
    if voice not in VOICES:
        raise SystemExit(f"Voz desconhecida: {voice}. Opções: {', '.join(VOICES)}")
    PIPER_DIR.mkdir(parents=True, exist_ok=True)
    if not PIPER_EXE.exists():
        log("1/2  Baixando o Piper…")
        data = download(PIPER_ZIP)
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            root = PIPER_DIR.resolve()
            for info in zf.infolist():
                # O zip traz tudo dentro de "piper/"; tira esse prefixo e não deixa sair da pasta.
                rel = info.filename.split("/", 1)[1] if "/" in info.filename else info.filename
                if not rel or info.is_dir():
                    continue
                target = (PIPER_DIR / rel).resolve()
                if root not in target.parents:
                    raise SystemExit(f"Caminho inválido no zip: {info.filename}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
        log("     Piper instalado em", PIPER_DIR)
    else:
        log("1/2  Piper já instalado.")
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    onnx = voice_file(voice)
    if not (onnx.exists() and onnx.with_suffix(".onnx.json").exists()):
        log(f"2/2  Baixando a voz '{voice}'…")
        cfg = download(VOICES[voice] + ".json")
        model = download(VOICES[voice])
        onnx.with_suffix(".onnx.json").write_bytes(cfg)
        onnx.write_bytes(model)   # o modelo por último: só existe se o download terminou
        log("     Voz instalada:", onnx.name)
    else:
        log(f"2/2  Voz '{voice}' já instalada.")
    return status()


def main():
    ap = argparse.ArgumentParser(description="Instala o Piper e uma voz pt-BR para o Alava Vision")
    ap.add_argument("--voz", default="faber", choices=list(VOICES))
    ap.add_argument("--verificar", action="store_true")
    a = ap.parse_args()
    st = status() if a.verificar else install(a.voz)
    log(f"Piper: {'instalado' if st['piper'] else 'não instalado'} · vozes: {', '.join(st['voices']) or 'nenhuma'}")
    # Código de saída 0 = pronto para falar (o instalar.bat usa isso no --verificar)
    sys.exit(0 if st["piper"] and st["voices"] else 1)


if __name__ == "__main__":
    main()
