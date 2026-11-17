# Changelog — Alava Vision

Todas as mudanças relevantes neste workspace são documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## Sistema Unificado

### [0.3.0] — 2026-11-17
> Backup da versão anterior: `backup_v0.2.0_20261117/` (código + banco). Como reverter: ver README.

#### Adicionado
- **Várias playlists**: criar, renomear e excluir. Os itens existentes foram migrados automaticamente para a "Playlist padrão".
- **Programação (timeline)** de 00:00 a 23:59 no painel:
  - régua de horários, zoom por hora, 30 min ou 15 min, linha vermelha do horário atual e botão "Ir para agora";
  - trilha base (playlists) e trilha de sobreposição (itens avulsos);
  - arrastar da biblioteca para a timeline, mover blocos, redimensionar pelas bordas e editar horários por número;
  - blocos sobrepostos na mesma trilha ficam em sub-faixas: encaixe total aparece em amarelo (informativo) e sobreposição parcial em vermelho (conflito), sempre dizendo qual bloco vale;
  - salvamento automático e selo "NO AR" no bloco em exibição.
- **Regra de prioridade**: item avulso > playlist agendada > Playlist padrão; na mesma trilha, vence o bloco que começa mais tarde.
- `GET /api/player/state`: o servidor decide o que a TV exibe agora. O player troca de conteúdo sozinho quando a programação muda de bloco.
- **Pré-visualização** de itens: imagem em proporção real com tamanho original; vídeo com controles; sites e widgets renderizados em 1920×1080 e reduzidos (iframe com sandbox). Disponível na lista, na biblioteca, no bloco selecionado e no cadastro de URL. Miniaturas de imagem e vídeo na lista.
- **Marca d'água Alava** no canto superior esquerdo de tudo o que a TV exibe (`assets/watermark.png`, gerado a partir de "Alava Cont Logo Branca.png"). Opacidade 0.8 e sombra dupla. Pode ser desligada com `--no-watermark` e ajustada com `--wm-opacity`.
- Cabeçalho de documentação (versão, como rodar, como reverter, mapa do código) em `server.py`, `player.py`, `static/index.html` e `static/weather.html`.

#### Corrigido
- **Chance de chuva** na tela de clima: o "92% no dia" era o `precipitation_probability_max` do Open-Meteo, a maior probabilidade horária do dia inteiro, incluindo horas que já passaram. Agora a tela mostra "X% nesta hora" e "máx. Y% até o fim do dia", calculado só com as horas restantes, cada informação em sua própria linha.
- Reordenar itens arrastando não salvava: a rota `/api/items/reorder` era capturada por `/api/items/{id}`.
- Data na tela de clima com maiúsculas erradas ("Terça-Feira, 17 De Novembro").
- "Nascer · pôr do sol" quebrava no meio; agora usa o mesmo padrão de valor + detalhe.
- Uploads servidos com proteção contra caminhos fora da pasta (`StaticFiles`).

#### Alterado
- Na tela de clima, a cidade foi para o canto superior direito, liberando o esquerdo para a marca d'água.

### [0.2.0] — 2026-11-17
#### Adicionado
- Tela de clima nova (`static/weather.html`): relógio, clima atual, previsão de 7 dias com probabilidade e volume de chuva
- Céu animado em canvas conforme a condição: sol se movendo do nascer ao pôr, nuvens, nublado, nevoeiro, chuva, tempestade com raios, neve, noite com lua e estrelas
- Vento acelera as nuvens, inclina a chuva e mostra rajadas na tela
- Alertas oficiais do INMET (filtrados por código IBGE) no canto inferior direito
- Endpoint `/api/weather` com cache de 10 minutos
- Configuração do código IBGE e atalhos de pré-visualização de cenários no painel

### [0.1.0] — 2026-11-17
#### Adicionado
- Servidor FastAPI + SQLite, painel web com login, player Chrome via CDP
- Tipos de conteúdo: site, imagem, vídeo, clima, trânsito e mensagem com janela de horário
- Projetos antigos movidos para `Old/`

## [Não lançado] — Próximos passos

> Próxima fase: integrar AlavaVision e Kiosk Player em um único sistema distribuído.

### Planejado
- Backend FastAPI com REST API e WebSocket
- Admin SPA web (substitui o app desktop Qt)
- Player unificado: Chrome via CDP para URLs + Qt para conteúdo local
- Comunicação push via WebSocket (substitui polling de 5s)
- Suporte a múltiplos players distribuídos em rede
- Widget de Vídeo (MP4, WebM)
- Widget de HTML local
- Widget de Contador Regressivo
- Autenticação e controle de permissões
- Métricas em tempo real

---

## AlavaVision

### [0.1.0] — 2026-08-13

#### Adicionado
- Estrutura completa do projeto (`core/`, `admin/`, `player/`, `data/`, `logs/`, `tests/`)
- Configuração `pyproject.toml`, `requirements.txt`, `.env`
- **Core — Database**: SQLite singleton com SQLAlchemy 2.0, WAL mode, foreign keys
- **Core — Modelos ORM**: Widget, Playlist, PlaylistItem, Alert, ScheduleRule, BrowserProfile, File, Audio, Log, Setting, Player
- **Core — Schemas Pydantic**: validação para Widget, Playlist, Alert, BrowserProfile
- **Core — Widgets**: BaseWidget (abstrato), SiteWidget, ImageWidget, TextWidget, ClockWidget, PDFWidget (PyMuPDF), WeatherWidget (OpenWeatherMap)
- **Core — Serviços**: ScheduleEngine (horário, dia da semana, intervalo de datas, data específica), LogService (logging estruturado por categoria), ConfigService (via dotenv)
- **Admin (PySide6)**: janela principal com abas — Dashboard, Widgets CRUD, Playlists com drag-and-drop, Alertas, Perfis de navegador, Agendamentos, Configurações, Logs
- **Admin — Controllers**: AlertController, PlaylistController, WidgetController, BrowserProfileController
- **Player**: PlayerEngine com loop de reprodução contínuo, polling de mudanças (5s), tratamento de erros e recuperação automática
- **Player — Renderers**: BaseRenderer (abstrato), SiteRenderer (QWebEngineView), ImageRenderer (QPixmap), TextRenderer (QLabel), PDFRenderer, ClockRenderer, WeatherRenderer
- **Player — AlertManager**: fila de alertas com prioridade, overlays com animações (fade, slide, zoom), reprodução de áudio via QSoundEffect
- **Player — ScreenManager**: detecção de múltiplos monitores, seleção por índice com fallback
- Scripts de execução: `executar_admin.bat`, `executar_player.bat`
- Suíte de testes: `tests/test_core.py`

#### Tipos de widget implementados
| Tipo | Renderizador | Configuração |
|------|-------------|--------------|
| `site` | QWebEngineView | URL, zoom, auto-refresh, perfil de navegador |
| `image` | QPixmap | Caminho do arquivo, fit mode |
| `text` | QLabel | Conteúdo, fonte, cor, alinhamento |
| `pdf` | PyMuPDF | Caminho do PDF, avanço automático por página |
| `clock` | QLabel | Formato, fuso horário, estilo |
| `weather` | QLabel | Cidade, unidades, chave API OpenWeatherMap |

#### Tipos de alerta implementados
| Tipo | Posição |
|------|---------|
| `overlay_center` | Centro da tela |
| `banner_top` | Faixa superior |
| `banner_bottom` | Faixa inferior |
| `toast` | Canto inferior direito |

---

## Kiosk Player

### [1.0.0] — 2026-11-17 (data de referência do workspace)

> Versão estável. Arquitetura minimalista de 3 arquivos.

#### Adicionado
- **`server.py`**: servidor Flask, `GET /api/pages` (público) + `PUT /api/pages` (autenticação HTTP Basic), persistência em `data.json` com escrita atômica via arquivo temporário, versionamento por timestamp Unix
- **`admin.html`**: painel single-page sem dependências externas — adicionar/remover/reordenar URLs, configurar duração por item, ativar/desativar, exibir tempo total do ciclo
- **`player.py`**: rotação de páginas com Chrome real (modo CDP padrão) ou Playwright; auto-reload ao detectar mudança de versão (polling 5s); modo idle com tela de espera; suporte a Chrome e Edge; perfil persistente de navegador; reinicialização automática após crash
- Dois modos de operação: `cdp` (Chrome nativo, sem flags de automação) e `playwright` (compatibilidade com versões anteriores)
- Flags configuráveis: `--screen-x`, `--screen-y`, `--width`, `--height`, `--mode`, `--channel`, `--browser-path`, `--cdp-port`, `--profile`, `--api`

---

## Histórico de Análise

### 2026-11-17 — Auditoria comparativa

Realizada análise completa dos dois projetos para planejamento da integração:

- **AlavaVision** é mais rico em funcionalidades (6 tipos de widget, agendamento, alertas, logging) mas limitado a um único PC por usar SQLite compartilhado
- **Kiosk Player** é mais simples e distribuído por natureza (REST API), usa Chrome real evitando bloqueios por automação, mas suporta apenas URLs
- A integração deve combinar: API REST do Kiosk + riqueza de tipos do AlavaVision + ScheduleEngine + AlertManager + Chrome via CDP para URLs
- O painel web do Kiosk Player é a abordagem correta para administração (acessível de qualquer dispositivo, sem instalação)
