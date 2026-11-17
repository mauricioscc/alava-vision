# Alava Vision — TV corporativa / Digital Signage

Painel web para montar o que passa na TV e um player que exibe esse conteúdo em tela cheia no segundo monitor.
Versão atual: **0.3.0** (histórico em [CHANGELOG.md](CHANGELOG.md)).

## Como rodar

```bash
pip install -r requirements.txt

# 1. Servidor + painel  →  http://localhost:8080/   (senha = ADMIN_PASSWORD do .env)
python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload

# 2. Player (na máquina ligada à TV)
python player.py --screen-x 1920        # TV à direita de um monitor de 1920px; use 0 se só houver a TV
```

Atalhos no Windows: `iniciar_servidor.bat` e `iniciar_player.bat`.

Opções úteis do player: `--port 8080`, `--width 1920 --height 1080`, `--channel msedge`,
`--no-watermark`, `--wm-opacity 0.7`, `--logo assets/outro.png`.

## O que o painel faz

| Aba | Para quê |
|---|---|
| **Playlists** | Criar playlists e adicionar sites, imagens, vídeos, clima, trânsito e mensagens. Arrastar para reordenar, ativar/desativar, pré-visualizar. |
| **Programação** | Timeline de 00:00 a 23:59. Arraste playlists e itens da biblioteca, mova, redimensione pelas bordas ou digite os horários. |
| **Configurações** | Cidade, coordenadas e código IBGE (clima e alertas do INMET), chave do Google Maps, cenários de teste da tela de clima. |

### Como a TV decide o que exibir

1. **Item avulso** agendado no horário: só ele aparece (sobrepõe a playlist).
2. Senão, a **playlist** agendada no horário.
3. Fora de qualquer bloco: a **Playlist padrão**. Sem nenhuma programação, o sistema funciona como na 0.2.0.

Dois blocos na mesma trilha no mesmo horário: vale o que começa mais tarde (o mais curto, se começarem juntos).
Para conferir a decisão atual: `http://localhost:8080/api/player/state`.

## Estrutura

```
Alava Vision/
├── server.py              Backend FastAPI + SQLite (API, programação, clima, telas do player)
├── player.py              Chrome em kiosk via CDP; segue /api/player/state; injeta a marca d'água
├── static/index.html      Painel administrativo
├── static/weather.html    Tela de clima (relógio, 7 dias, céu animado, alertas INMET)
├── assets/                Logos da Alava; watermark.png é a versão usada na TV
├── data/                  Banco (database.db), uploads e perfil do navegador do player
├── .env                   Senha, porta, localização, código IBGE
├── backup_v0.2.0_20261117/  Cópia da versão anterior (código + banco)
└── Old/                   Projetos originais (AlavaVision em Qt e kiosk-player)
```

Cada arquivo de código começa com um bloco de comentários com a versão, como rodar, como reverter e um mapa
de onde fica cada funcionalidade.

## Como reverter para a 0.2.0

1. Pare o servidor e o player.
2. Copie `server.py`, `player.py` e `static/` de `backup_v0.2.0_20261117/` por cima dos atuais.
3. Opcional: copie `backup_v0.2.0_20261117/data/database.db*` para `data/` para voltar o banco ao estado anterior.
   Sem esse passo, a versão antiga também funciona com o banco novo, porque as tabelas novas são ignoradas.

## Limitações conhecidas

- **Prévia de sites**: alguns sites (ex.: sistemas com login) não permitem ser exibidos dentro de outra página.
  A prévia mostra um aviso nesses casos; na TV eles abrem normalmente.
- **Marca d'água**: sites com política de segurança que bloqueia imagens `data:` não exibem o logo.
- **Alertas do INMET**: o endereço usado (`apiprevmet3.inmet.gov.br/avisos/ativos`) não é documentado oficialmente.
  Se sair do ar, a tela de clima continua funcionando, só sem os alertas.
- A programação é diária (igual todos os dias) e usa o relógio do computador do servidor.
