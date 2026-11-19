# Alava Vision — TV corporativa / Digital Signage

Painel web para montar o que passa na TV e um player que exibe esse conteúdo em tela cheia no segundo monitor.
Versão atual: **0.17.1** (histórico em [CHANGELOG.md](CHANGELOG.md)).

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
| **Relatório**     | O que passou na TV (0.17.0): por item (quantas vezes, tempo no ar, quantas vezes foi interrompido e por quê), a linha do tempo e as manchetes exibidas. Hoje, ontem, 7 ou 30 dias ou um período; **⬇ Planilha** baixa em CSV (abre no Excel). Guarda 90 dias. |
| **Calendário**    | O mês inteiro: qual régua vale em cada dia, feriados, datas comemorativas, avisos e playlists agendadas. Clique num dia para **adicionar um aviso**, criar uma exceção (ex.: feriado), pôr uma playlist o dia todo ou abrir a régua. |
| **Configurações** | Cidade, coordenadas e código IBGE (clima e alertas do INMET), chave do Google Maps, cenários de teste da tela de clima.                      |

### Tipos de item com opções especiais

- **Vídeo:** a opção *Repetir* (ligada por padrão) faz o vídeo recomeçar até completar a duração do item. Desligada, ele toca uma vez e a TV passa para o próximo item assim que o vídeo acaba. O painel mostra quanto tempo o vídeo tem e oferece usar esse tempo como duração.
- **Mensagem:** título opcional, fundo em cor sólida, degradê ou imagem (com escurecimento), fonte, alinhamento, negrito, sombra e animação de entrada. O formulário mostra uma prévia ao vivo, do tamanho da TV.
- **Ler a mensagem em voz alta:** marque *🔊 Ler a mensagem em voz alta* no formulário (voz, velocidade, texto próprio para leitura e botão *▶ Ouvir*). A voz é o Piper, que roda no próprio computador, sem internet. Instale uma vez, no computador da TV, em **Configurações → Voz → Instalar voz** (~85 MB), pelo `instalar.bat` ou com `python ferramentas/instalar_voz.py`.
- **Buscar imagens na web** (fundo da mensagem e itens de imagem): pesquisa pelo **nome do item**, por isso dê um nome antes de buscar. Sem configuração, usa o Openverse (imagens de licença livre). Para fotos mais profissionais, crie uma chave gratuita em pexels.com/api e coloque `PEXELS_API_KEY=` no `.env`. A imagem escolhida fica salva no computador, com o crédito do autor no canto da tela.
- **Clima:** a condição de agora (ícone, texto e fundo animado) é a **observada** no aeroporto mais próximo (boletim METAR), não a estimada pela previsão. A previsão de 7 dias continua vindo da Open-Meteo. Para fixar o aeroporto, use `METAR_STATION=` no `.env` (ex.: `SBJR`). A chuva tem cenário próprio de dia (com sol e arco-íris) e de noite (com a lua e o brilho da cidade).
- **Atualizar pelo painel (0.14.0):** em Configurações → 🔄 Sistema, **Verificar atualização** mostra o que há de novo no GitHub, e **Atualizar agora** baixa a versão nova e reinicia o servidor e a TV sozinho (a página recarrega quando termina). O resultado fica em `data/update.log`. Dar dois cliques no `atualizar.bat` continua funcionando.
- **Trânsito:** na TV o player abre o Waze direto (com a faixa da Alava por cima), porque dentro de outra página o Waze não mostra as linhas de trânsito no Chrome do player.
- **Hoje é dia:** cada card fica *Segundos por card* na tela (padrão 30 s); o item fica o tempo de mostrar todos os cards do dia.
- **Avisos da TV (0.15.0):** se um site (ex.: Acessórias) cair na tela de login ou o Waze não carregar o trânsito, a TV pula o item e o painel mostra uma faixa amarela com o que fazer. Para refazer o login do Acessórias, dê dois cliques em `ferramentas\login_na_tv.bat` no computador da TV.
- **Notícias (RSS):** uma manchete por vez, com foto e resumo. Escolha as fontes prontas (g1, Agência Brasil, BBC, ge, InfoMoney) ou cole qualquer feed RSS. Cada card fica **30 segundos** na tela por padrão: o tempo do item é *Segundos por card* × *Cards por vez* (o campo Duração não aparece nesse tipo). No rodapé, alternando a cada 15 s, a **cotação do dólar** e os **indicadores** (Euro, Selic, CDI, IPCA e IGP-M 12 meses). A cotação do dólar (comercial ao vivo, gráfico de 30 dias e PTAX do Banco Central), que atualiza sozinha e pode ser desligada no item. O filtro de palavras esconde notícias de crimes e tragédias (lista editável), e o botão **Testar feeds** mostra o que vai aparecer antes de salvar.
  - **Foco contábil (0.13.0):** as fontes do **Portal Contábeis** (últimas notícias, notícias publicadas e legislação), o **Jornal Contábil**, o **CFC** e a **FENACON** já vêm prontas e marcadas como **Preferenciais**. O Contábeis — Artigos e o ConJur — Tributário estão na lista, só marcar. As fontes se revezam na fila, então nenhuma ocupa todas as vagas. Cada fonte tem uma **Prioridade** (Alta / Normal / Baixa), um liga/desliga e o botão **Testar feed**, que diz quantas notícias foram lidas e quantas são aproveitáveis.
  - **Como a fila é montada:** com pelo menos uma fonte de prioridade Alta, 3 de cada 4 notícias vêm das preferenciais e 1 das demais (ajustável: só preferenciais, 75% ou 50%). Matérias com palavras como *Receita Federal, Simples Nacional, IRPF, eSocial, Reforma Tributária, ICMS, SPED, prazo* sobem na fila (lista editável). A mesma matéria em dois feeds aparece uma vez só, e notícias mais velhas que o limite (30 dias) são ignoradas.
  - **Sem repetir (0.16.0):** a TV anota cada manchete que mostrou (`data/news_seen.json`) e não repete por **3 dias**, valendo para todos os itens de notícias juntos (a Manhã não repete o que a Tarde já mostrou). Se um dia as novas acabarem, volta primeiro a que passou há mais tempo. A prévia do painel não conta como exibida. Para recomeçar, use **↺ Zerar histórico** no formulário do item de notícias.
  - **Na TV:** um selo mostra `FONTE • CATEGORIA` (ex.: *PORTAL CONTÁBEIS • TRIBUTÁRIO*) e, quando a matéria não tem foto, aparece a logo da Alava no lugar.
  - **Sem internet:** o servidor guarda as notícias em `data/news_cache.json` e continua mostrando as últimas lidas. O tempo de cache é `NEWS_TTL` no `.env` (padrão 600 s).
  - **Atenção:** o feed `/rss/legislacao/` do Contábeis está parado em novembro de 2020. Enquanto for assim, o **Testar feed** mostra "nenhuma aproveitável" e nenhuma legislação entra na fila (de propósito: não aparece lei de 2020 como se fosse novidade). Se ele voltar a publicar, passa a entrar sozinho.
- **📅 Hoje é dia (curiosidades):** "Hoje é Dia do Professor", feriado do dia e "Faltam 3 dias para o feriado". Ponha o item numa playlist ou ligue em **Configurações → Curiosidades e datas** a opção *Aparecer curiosidades durante o horário de serviço*, que intercala a tela na playlist a cada N minutos. A lista de datas é editável ali mesmo, no formato `DD/MM | Título | Texto`, também com datas móveis como `2º domingo/05`. Os feriados nacionais vêm sozinhos da BrasilAPI.
- **📣 Avisos por data** (Calendário → clique no dia → *Adicionar aviso para este dia*): mensagem, imagem, contador ou "Hoje é dia", já preenchidos a partir do feriado ou da data comemorativa. Escolha quantos dias antes começa a aparecer, o horário (o dia todo ou só no expediente) e se repete todo ano. Datas móveis como Carnaval e Dia das Mães são acompanhadas sozinhas. O aviso é **intercalado** no que estiver no ar, inclusive durante um item avulso, sem mudar a programação.
- **🧾 Agenda fiscal (0.17.0):** os vencimentos dos próximos dias (padrão 10), agrupados por data, com *HOJE*, *AMANHÃ* ou *EM N DIAS*, e a nota quando o prazo mudou por feriado ou fim de semana ("Antecipado: 20/11 é feriado"). Já vêm eSocial e EFD-Reinf (dia 15), salários (5º dia útil), FGTS Digital, INSS e IRRF (dia 20, antecipam), DAS/PGDAS-D e DAS-MEI (dia 20, prorrogam), PIS/Cofins (dia 25), DCTFWeb e IRPJ/CSLL (último dia útil), 13º salário e os anuais (DEFIS, IRPF, DASN-SIMEI, ECD, ECF). Ligue ou desligue cada um no item e acrescente os prazos do escritório, um por linha: `ISS Rio | 10 | prorroga`, `Alvará | 31/01 | antecipa`, `Balancete | último dia útil`. O botão **Ver a lista que vai para a TV** mostra o resultado antes de salvar. Dia útil = segunda a sexta menos os feriados nacionais (feriado municipal não entra). Os prazos ficam em `FISCAL_RULES`, no `server.py`.
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

No topo da aba Programação, **Na TV agora** mostra o item na tela, quanto falta e o próximo. O botão
**⏭ Pular item** passa a TV para o próximo item na hora, e **⏮ Voltar item** volta para o anterior (0.16.0).
Quando a TV está nas notícias, aparecem também **◀ Notícia anterior** e **Próxima notícia ▶**, que trocam só a
manchete (o item continua no ar).

Ao lado fica a **foto da TV** (0.16.0): o player tira uma foto da tela a cada 5 minutos e o painel mostra
"Última atualização em HH:MM". Clique na foto para ampliar. A foto fica só na memória do servidor (some ao
reiniciar) e só aparece para quem entrou com a senha do painel.

**📢 Aviso urgente** (0.17.0), no mesmo cartão: escreva um texto (ou escolha uma sugestão, como "Cliente na
recepção"), escolha por quanto tempo (1 min a 1 h) e a cor (atenção, urgente ou aviso). A TV interrompe o que estiver
passando, mostra o aviso em tela cheia e, quando o tempo acaba ou alguém clica em **Encerrar aviso** (ou em *Pular
item*), volta para o item que foi interrompido. O aviso fica só na memória do servidor: reiniciar encerra.

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
