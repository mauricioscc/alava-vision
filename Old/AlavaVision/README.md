# AlavaVision - Sistema de TV Corporativa / Digital Signage

Sistema modular de Digital Signage desenvolvido em Python com PySide6.

## Arquitetura

```
alavavision/
├── core/              # Código compartilhado (modelos, serviços, widgets)
├── admin/             # Aplicação Administrador (PySide6)
│   ├── controllers/   # Lógica de negócio (CRUD)
│   └── views/         # Interface gráfica
├── player/            # Aplicação Player (fullscreen kiosk)
│   └── renderers/     # Renderizadores de cada tipo de widget
├── server/            # API REST (futuro)
├── data/              # Dados em runtime (DB, arquivos, perfis)
├── logs/              # Logs do sistema
└── tests/             # Testes automatizados
```

## Requisitos

- Python 3.12+
- PySide6 6.6+
- SQLAlchemy 2.0+
- Pydantic 2.0+

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

### Administrador

```bash
python -m admin.app
```

Interface gráfica para gerenciar:
- **Widgets**: Site, Imagem, Texto (e mais em breve)
- **Playlists**: Ordenação e duração dos conteúdos
- **Alertas**: Notificações sobrepostas
- **Agendamentos**: Regras de exibição
- **Perfis de Navegador**: Sessões persistentes
- **Configurações**: Ajustes do sistema
- **Logs**: Visualização de eventos

### Player

```bash
python -m player.app
```

Player fullscreen que:
- Exibe no monitor secundário (configurável via `.env`)
- Executa a playlist em loop
- Respeita duração e regras de cada widget
- Suporta alertas sobrepostos
- Mantém sessões de navegador persistentes
- Tolerante a falhas (avança se um widget falhar)

## Widgets Implementados (MVP)

| Tipo | Descrição | Configuração |
|------|-----------|--------------|
| **Site** | Páginas web com QWebEngineView | URL, zoom, auto-refresh, perfil de navegador |
| **Imagem** | PNG, JPG, WebP, GIF | File path, fit mode |
| **Texto** | Texto estilizado | Conteúdo, fonte, cor, alinhamento |

## Widgets Futuros

- Vídeo (MP4, WebM)
- PDF
- HTML local
- Relógio
- Contador regressivo

## Regras de Exibição

O ScheduleEngine avalia regras como:
- **Horário**: Exibir entre 08:00 e 18:00
- **Dias**: Segunda a sexta
- **Data**: Período específico
- **Prioridade**: Widgets com maior prioridade interrompem a playlist

## Alertas

Tipos suportados:
- Overlay central
- Banner superior/inferior
- Toast
- Ticker (texto rolante)

Animações: Fade, Slide, Zoom

## Comunicação Admin ↔ Player

**MVP**: SQLite compartilhado (mesmo computador)

**Futuro**: API REST + WebSocket (servidor central, múltiplos players)

## Estrutura do Banco

- `widgets` - Conteúdos
- `playlists` / `playlist_items` - Playlists ordenadas
- `alerts` - Alertas
- `schedule_rules` - Regras de exibição
- `browser_profiles` - Perfis de navegador
- `files` / `audios` - Mídia
- `players` - Dispositivos
- `settings` - Configurações
- `logs` - Eventos

## Testes

```bash
python tests/test_core.py
```

## Licença

Proprietário - AlavaVision