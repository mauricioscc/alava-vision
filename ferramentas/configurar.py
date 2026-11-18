"""
Alava Vision — Configuração do .env (ferramentas/configurar.py) · versão 0.7.0

Pergunta a senha do painel, a porta e o monitor da TV e grava o .env.
É chamado pelo instalar.bat, mas pode ser rodado sozinho para mudar essas três coisas.

COMO RODAR
    python ferramentas\\configurar.py              # cria ou edita o .env da pasta do projeto
    python ferramentas\\configurar.py --env X.env  # outro arquivo (usado nos testes)

O QUE ELE FAZ
    • .env ainda não existe: parte do .env.example.
    • .env já existe: mostra os valores atuais, Enter mantém. As outras linhas
      (cidade, chave do Google Maps etc.) não são tocadas.
    • Porta: confere se já está em uso neste computador e sugere uma livre (8090 em diante).
    • Monitor: lista os monitores na mesma numeração do player (1 = principal).
    Cidade, coordenadas e código IBGE ficam na aba Configurações do painel.

COMO REVERTER
    git checkout <commit> -- ferramentas/configurar.py   (ou apague a pasta ferramentas/)

MAPA DO CÓDIGO
    Leitura do .env ......... read_env()
    Porta em uso ............ port_in_use(), ask_port()
    Senha ................... ask_password()  (sem espaço, # ou aspas, que quebrariam o .env)
    Monitor ................. ask_monitor()   (usa monitors.py)
    Gravação ................ write_env()     (troca só as linhas que mudaram; UTF-8 sem BOM)
    Endereço na rede ........ local_ip()
"""
import argparse
import socket
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

PLACEHOLDER = "troque-esta-senha"
FORBIDDEN = set(' \t#"\'')


def read_env(path: Path) -> dict:
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        values[k.strip()] = v.strip().strip("'\"")
    return values


def port_in_use(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", port)) == 0:
            return True
    try:
        with socket.socket() as s:
            s.bind(("0.0.0.0", port))
    except OSError:
        return True
    return False


def ask(prompt: str, default="") -> str:
    shown = f" [{default}]" if str(default) != "" else ""
    return input(f"{prompt}{shown}: ").strip() or str(default)


def yes(prompt: str, default: bool) -> bool:
    v = input(f"{prompt} ({'S/n' if default else 's/N'}): ").strip().lower()
    return default if not v else v.startswith("s")


def ask_password(current: str | None) -> str:
    keep = bool(current) and current != PLACEHOLDER
    while True:
        v = input("Senha do painel" + (" (Enter mantém a atual)" if keep else "") + ": ").strip()
        if not v and keep:
            return current
        if not v:
            print("  A senha não pode ficar vazia.")
        elif v == PLACEHOLDER:
            print("  Escolha uma senha diferente da do exemplo.")
        elif len(v) < 6:
            print("  Use pelo menos 6 caracteres.")
        elif any(c in FORBIDDEN for c in v):
            print("  Não use espaço, # nem aspas na senha.")
        else:
            return v


def ask_port(current: str) -> int:
    default = int(current) if str(current).isdigit() else 8080
    if port_in_use(default):
        free = next((p for p in range(8090, 8200) if not port_in_use(p)), None)
        print(f"  A porta {default} já está em uso neste computador"
              + (f"; sugestão: {free}." if free else "."))
        default = free or default
    while True:
        v = ask("Porta do painel", default)
        if not v.isdigit() or not 1024 <= int(v) <= 65535:
            print("  Digite um número entre 1024 e 65535.")
            continue
        p = int(v)
        if port_in_use(p):
            print(f"  A porta {p} está em uso. Se for o próprio Alava Vision aberto, feche-o antes.")
            if not yes("  Usar essa porta mesmo assim?", False):
                continue
        return p


def ask_monitor(current: str) -> int:
    try:
        import monitors
        mons = monitors.list_monitors()
    except Exception:
        monitors, mons = None, []
    if mons:
        print("\nMonitores encontrados agora (a TV precisa estar ligada para aparecer):")
        for m in mons:
            print("  " + monitors.describe(m))
    default = current if str(current).isdigit() else ("1" if len(mons) == 1 else "2")
    while True:
        v = ask("Número do monitor da TV", default)
        if v.isdigit() and int(v) >= 1:
            return int(v)
        print("  Digite o número do monitor (1, 2, 3...).")


def write_env(path: Path, base: Path, old: dict, new: dict) -> None:
    lines = base.read_text(encoding="utf-8-sig").splitlines() if base.exists() else []
    changed = {k: str(v) for k, v in new.items() if old.get(k) != str(v)}
    out, done = [], set()
    for line in lines:
        s = line.strip()
        key = s.split("=", 1)[0].strip() if "=" in s and not s.startswith("#") else None
        if key in changed:
            out.append(f"{key}={changed[key]}")
            done.add(key)
        else:
            out.append(line)
    out += [f"{k}={v}" for k, v in changed.items() if k not in done and k not in old]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def local_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Configura o .env do Alava Vision")
    ap.add_argument("--env", type=Path, default=BASE / ".env")
    env_path = ap.parse_args().env
    existed = env_path.exists()
    base = env_path if existed else BASE / ".env.example"
    old = read_env(base)

    print("\nConfiguração do Alava Vision")
    print("-" * 28)
    if existed:
        print(f"O .env já existe ({env_path}). Enter mantém cada valor atual.\n")
    pwd = ask_password(old.get("ADMIN_PASSWORD") if existed else None)
    port = ask_port(old.get("PORT", "8080"))
    mon = ask_monitor(old.get("PLAYER_MONITOR", "2"))

    write_env(env_path, base, old if existed else {}, {"ADMIN_PASSWORD": pwd, "PORT": port, "PLAYER_MONITOR": mon})
    ip = local_ip()
    print(f"\n.env salvo em {env_path}")
    print(f"Painel neste computador ...... http://localhost:{port}/   (usuário admin)")
    if ip:
        print(f"Painel de outro computador ... http://{ip}:{port}/")
    print("Cidade, coordenadas e código IBGE: aba Configurações do painel.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nConfiguração cancelada; o .env não foi alterado.")
        sys.exit(1)
