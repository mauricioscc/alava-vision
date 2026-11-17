# Alava Vision — TV corporativa / Digital Signage

Painel web para montar o que passa na TV e um player que exibe esse conteúdo em tela cheia no segundo monitor.
Versão atual: **0.5.0** (histórico em [CHANGELOG.md](CHANGELOG.md)).

## Como rodar

Primeira vez: `pip install -r requirements.txt` e copie `.env.example` para `.env` (defina a senha).

**Na máquina da TV (um clique):** `iniciar_alava_vision.bat` sobe o servidor e abre o player em tela cheia no
monitor da TV. Para iniciar junto com o Windows, coloque um atalho desse arquivo em `shell:startup`
(Win+R → `shell:startup`).

Manualmente:

```bash
# 1. Servidor + painel  →  http://localhost:8080/   (senha = ADMIN_PASSWORD do .env)
python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload

# 2. Player: abre sempre no monitor 2 (onde a TV fica ligada pelo HDMI)
python player.py
python player.py --list-monitors     # confere a numeração dos monitores
```

### Monitor da TV

O player pergunta ao Windows onde está cada tela e abre o Chrome em tela cheia no **monitor 2**
(1 = principal; 2, 3… = os demais, da esquerda para a direita). Não importa a resolução, a escala
nem a posição das telas nas configurações do Windows.

- Para outro monitor: `PLAYER_MONITOR=3` no `.env` ou `python player.py --monitor 3`.
- A cada 10 s ele confere a janela. Se ela saiu da TV, volta para lá.
- TV desligada ou desconectada: a janela é minimizada para não cobrir o monitor principal e volta sozinha quando a TV reaparece.

Outras opções do player: `--port 8080`, `--channel msedge`, `--monitor 0 --screen-x X --screen-y Y` (posição manual).

### Logo da Alava

O logo aparece no canto superior esquerdo apenas nas telas de **clima** e **trânsito**. Sites, imagens,
vídeos e mensagens aparecem sem alteração. O arquivo usado é `assets/watermark.png`.

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
├── player.py              Chrome em kiosk via CDP; segue /api/player/state
├── monitors.py            Detecta os monitores do Windows e mantém a janela do player na TV
├── iniciar_alava_vision.bat  Servidor + player com um clique
├── static/index.html      Painel administrativo
├── static/weather.html    Tela de clima (relógio, 7 dias, céu animado, alertas INMET)
├── assets/                Logos da Alava; watermark.png é o logo das telas de clima e trânsito
├── data/                  Banco (database.db), uploads e perfil do navegador do player
├── .env                   Senha, porta, localização, código IBGE, monitor da TV (fora do Git)
├── .env.example           Modelo do .env
├── backup_v0.2.0_20261117/  Cópia da versão anterior (código + banco)
└── Old/                   Projetos originais (AlavaVision em Qt e kiosk-player)
```

Cada arquivo de código começa com um bloco de comentários com a versão, como rodar, como reverter e um mapa
de onde fica cada funcionalidade.

## Versões e como reverter

O projeto usa Git a partir da 0.3.0. `main` é a versão estável; mudanças novas são feitas numa branch.

```bash
git log --oneline              # lista as versões
git checkout main              # volta para a versão estável
git checkout <commit> -- player.py   # restaura só um arquivo de uma versão anterior
```

Ficam fora do Git: `.env` (senha), `data/` (banco, uploads e login do Chrome da TV) e as pastas de backup.

### Voltar para a 0.2.0 (anterior ao Git)

1. Pare o servidor e o player.
2. Copie `server.py`, `player.py` e `static/` de `backup_v0.2.0_20261117/` por cima dos atuais.
3. Opcional: copie `backup_v0.2.0_20261117/data/database.db*` para `data/` para voltar o banco ao estado anterior.
   Sem esse passo, a versão antiga também funciona com o banco novo, porque as tabelas novas são ignoradas.

## Limitações conhecidas

- **Prévia de sites**: alguns sites (ex.: sistemas com login) não permitem ser exibidos dentro de outra página.
  A prévia mostra um aviso nesses casos; na TV eles abrem normalmente.
- **Alertas do INMET**: o endereço usado (`apiprevmet3.inmet.gov.br/avisos/ativos`) não é documentado oficialmente.
  Se sair do ar, a tela de clima continua funcionando, só sem os alertas.
- A programação é diária (igual todos os dias) e usa o relógio do computador do servidor.
