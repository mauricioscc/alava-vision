# Alava Vision — TV corporativa / Digital Signage

Painel web para montar o que passa na TV e um player que exibe esse conteúdo em tela cheia no segundo monitor.
Versão atual: **0.12.0** (histórico em [CHANGELOG.md](CHANGELOG.md)).

## Como rodar

### No computador da TV

Pré-requisitos: **Python 3.10+** (marque "Add Python to PATH" na instalação), **Git** e **Google Chrome**.

1. Baixe o projeto (o repositório é privado: o Git pede o login do GitHub na primeira vez):
   ```
   git clone https://github.com/mauricioscc/alava-vision.git "C:\Alava Vision"
   ```
2. Dê dois cliques em **`instalar.bat`**. Ele confere Python, Git e Chrome, instala as bibliotecas,
   pergunta a senha do painel, a porta (avisa se já estiver em uso) e o monitor da TV, e oferece
   iniciar com o Windows.

| Arquivo                      | Para quê                                                                                                                                                      |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instalar.bat`             | Instalação (uma vez). Pode ser rodado de novo: mantém o `.env` e os dados.                                                                                |
| `iniciar_alava_vision.bat` | Abre o servidor e, quando ele responde, o player na TV.                                                                                                        |
| `atualizar.bat`            | Fecha o sistema, baixa a versão nova do GitHub (`git pull`), atualiza as bibliotecas, mostra as novidades e reabre. Não mexe no `.env` nem em `data/`. |
| `startup.bat`              | Liga ou desliga o início automático com o Windows (atalho em `shell:startup` para o `iniciar_alava_vision.bat`).                                         |

O início automático acontece quando o usuário entra no Windows. Para a TV voltar sozinha depois de uma queda
de energia, o PC precisa entrar no Windows sem senha (login automático) e ligar sozinho quando a energia volta
(opção da BIOS).

Para mudar só a senha, a porta ou o monitor depois: `python ferramentas\configurar.py`.

Manualmente:

```bash
# 1. Servidor + painel  →  http://localhost:8080/   (senha = ADMIN_PASSWORD do .env)
python -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload

# 2. Player: abre sempre no monitor 2 (onde a TV fica ligada pelo HDMI)
python player.py
python player.py --list-monitors     # confere a numeração dos monitores
```

### Porta

O padrão é a **8080**. Se ela já estiver em uso no computador, troque no `.env`:

```
PORT=8090
```

Os `.bat` e o player leem esse valor sozinhos. O painel passa a ser `http://localhost:8090/`.
Se você rodar o uvicorn manualmente, use a mesma porta no `--port`.

### Monitor da TV

O player pergunta ao Windows onde está cada tela e abre o Chrome em tela cheia no **monitor 2**
(1 = principal; 2, 3… = os demais, da esquerda para a direita). Não importa a resolução, a escala
nem a posição das telas nas configurações do Windows.

- Para outro monitor: `PLAYER_MONITOR=3` no `.env` ou `python player.py --monitor 3`.
- A cada 10 s ele confere a janela. Se ela saiu da TV, volta para lá.
- TV desligada ou desconectada: a janela é minimizada para não cobrir o monitor principal e volta sozinha quando a TV reaparece.

Outras opções do player: `--port 8080`, `--channel msedge`, `--monitor 0 --screen-x X --screen-y Y` (posição manual).

### Logo da Alava

O logo aparece no canto superior esquerdo das telas de **clima**, **trânsito** e **notícias** (nas notícias,
pode ser desligado no item). Sites, imagens, vídeos e mensagens aparecem sem alteração. O arquivo usado é `assets/watermark.png`.

## O que o painel faz

| Aba                       | Para quê                                                                                                                                      |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Playlists**       | Criar, renomear e **duplicar** playlists (com todos os itens); adicionar e **duplicar itens** (⧉, ou *Salvar e duplicar* no formulário); adicionar sites, imagens, vídeos, clima, trânsito, mensagens, contadores regressivos e páginas HTML locais. Arrastar para reordenar, ativar/desativar, pré-visualizar. |
| **Programação**   | Timeline de 00:00 a 23:59, uma por **régua**: *Todos os dias*, cada dia da semana ou uma data. Arraste playlists e itens da biblioteca, mova, redimensione pelas bordas ou digite os horários. Zoom livre: do dia inteiro na tela até 1 min, com Ctrl + roda do mouse, a roda sobre a faixa de horas ou a barra. **↻ Repetir nos dias úteis** copia a régua para segunda a sexta. |
| **Calendário**    | O mês inteiro: qual régua vale em cada dia, feriados, datas comemorativas, avisos e playlists agendadas. Clique num dia para **adicionar um aviso**, criar uma exceção (ex.: feriado), pôr uma playlist o dia todo ou abrir a régua. |
| **Configurações** | Cidade, coordenadas e código IBGE (clima e alertas do INMET), chave do Google Maps, cenários de teste da tela de clima.                      |

### Tipos de item com opções especiais

- **Vídeo:** a opção *Repetir* (ligada por padrão) faz o vídeo recomeçar até completar a duração do item. Desligada, ele toca uma vez e a TV passa para o próximo item assim que o vídeo acaba. O painel mostra quanto tempo o vídeo tem e oferece usar esse tempo como duração.
- **Mensagem:** título opcional, fundo em cor sólida, degradê ou imagem (com escurecimento), fonte, alinhamento, negrito, sombra e animação de entrada. O formulário mostra uma prévia ao vivo, do tamanho da TV.
- **Ler a mensagem em voz alta:** marque *🔊 Ler a mensagem em voz alta* no formulário (voz, velocidade, texto próprio para leitura e botão *▶ Ouvir*). A voz é o Piper, que roda no próprio computador, sem internet. Instale uma vez, no computador da TV, em **Configurações → Voz → Instalar voz** (~85 MB), pelo `instalar.bat` ou com `python ferramentas/instalar_voz.py`.
- **Buscar imagens na web** (fundo da mensagem e itens de imagem): pesquisa pelo **nome do item**, por isso dê um nome antes de buscar. Sem configuração, usa o Openverse (imagens de licença livre). Para fotos mais profissionais, crie uma chave gratuita em pexels.com/api e coloque `PEXELS_API_KEY=` no `.env`. A imagem escolhida fica salva no computador, com o crédito do autor no canto da tela.
- **Notícias (RSS):** uma manchete por vez, com foto e resumo. Escolha as fontes prontas (g1, Agência Brasil, BBC, ge, InfoMoney) ou cole qualquer feed RSS. O filtro de palavras esconde notícias de crimes e tragédias (lista editável), e o botão **Testar feeds** mostra o que vai aparecer antes de salvar.
- **📅 Hoje é dia (curiosidades):** "Hoje é Dia do Professor", feriado do dia e "Faltam 3 dias para o feriado". Ponha o item numa playlist ou ligue em **Configurações → Curiosidades e datas** a opção *Aparecer curiosidades durante o horário de serviço*, que intercala a tela na playlist a cada N minutos. A lista de datas é editável ali mesmo, no formato `DD/MM | Título | Texto`, também com datas móveis como `2º domingo/05`. Os feriados nacionais vêm sozinhos da BrasilAPI.
- **📣 Avisos por data** (Calendário → clique no dia → *Adicionar aviso para este dia*): mensagem, imagem, contador ou "Hoje é dia", já preenchidos a partir do feriado ou da data comemorativa. Escolha quantos dias antes começa a aparecer, o horário (o dia todo ou só no expediente) e se repete todo ano. Datas móveis como Carnaval e Dia das Mães são acompanhadas sozinhas. O aviso é **intercalado** no que estiver no ar, inclusive durante um item avulso, sem mudar a programação.
- **Contador regressivo:** título, data e hora do evento, cores e texto exibido quando a hora chega. Com *Tirar da TV depois que a hora chegar*, o item deixa de aparecer sozinho.
- **HTML local:** envie um `.html` (página única) ou um `.zip` com a página e seus arquivos (CSS, imagens, scripts). A página inicial do `.zip` é o `index.html`. Cada envio fica em `data/html/<id>/`.

### Tema do painel

O botão no topo do painel alterna entre **Automático** (segue o tema do Windows), **Claro** e **Escuro**.
A escolha fica salva no navegador. As telas da TV não mudam.

### Como a TV decide o que exibir

Primeiro, a **régua do dia**:

1. **Exceção da data** (criada no Calendário ou escolhendo a data na Programação);
2. senão, a **régua do dia da semana**, se aquele dia tiver uma própria;
3. senão, a régua **Todos os dias**.

A régua é escolhida inteira: um dia com régua própria ignora a de *Todos os dias*. Para mudar só um trecho,
crie a régua própria copiando a de *Todos os dias* (é o botão padrão) e edite só o que muda. Uma régua própria
vazia deixa o dia todo na Playlist padrão.

Depois, **dentro da régua**:

1. **Item avulso** agendado no horário: só ele aparece (sobrepõe a playlist).
2. Senão, a **playlist** agendada no horário.
3. Fora de qualquer bloco: a **Playlist padrão**. Sem nenhuma programação, o sistema funciona como na 0.2.0.

Dois blocos na mesma trilha no mesmo horário: vale o que começa mais tarde (o mais curto, se começarem juntos).
Para conferir a decisão atual: `http://localhost:8080/api/player/state`.

Salvar algo no painel não faz a TV recomeçar a playlist. O item na tela continua, e só aparece de novo se foi
ele o editado. A playlist só recomeça do 1º item quando a programação troca de bloco.

## Estrutura

```
Alava Vision/
├── server.py              Backend FastAPI + SQLite (API, programação, clima, telas do player)
├── player.py              Chrome em kiosk via CDP; segue /api/player/state
├── monitors.py            Detecta os monitores do Windows e mantém a janela do player na TV
├── iniciar_alava_vision.bat  Servidor + player com um clique
├── instalar.bat           Instalação no PC da TV (bibliotecas, .env, início com o Windows)
├── atualizar.bat          Fecha, baixa a versão nova (git pull) e reabre
├── startup.bat            Liga/desliga o início automático com o Windows
├── ferramentas/           configurar.py (.env interativo), instalar_voz.py (Piper + vozes; instala em ferramentas/piper/)
│                          e parar_alava_vision.ps1 (usado pelo atualizar)
├── conteudo/              datas_comemorativas.txt (lista padrão; a editável fica em data/)
├── static/index.html      Painel administrativo
├── static/weather.html    Tela de clima (relógio, 7 dias, céu animado, alertas INMET); abre já com a previsão
├── static/fonts/          Fonte Inter local usada na TV
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
  Se sair do ar, a tela de clima continua funcionando e mostra o aviso "INMET indisponível" no lugar dos alertas. Para ver o aviso sem derrubar nada: `/view/weather?inmet=off` (ou o atalho "INMET indisponível" em Configurações).
- A programação usa o relógio do computador do servidor. Exceções de datas que já passaram continuam guardadas (não atrapalham; dá para removê-las no Calendário).
