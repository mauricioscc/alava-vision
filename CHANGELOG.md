# Changelog — Alava Vision

Todas as mudanças relevantes neste workspace são documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## Sistema Unificado

### [0.11.0] — 2026-11-18
#### Adicionado
- **Programação por dia da semana.** A aba Programação ganhou o seletor **Régua**: *Todos os dias*, *Seg* a *Dom* e uma data específica.
  - Um dia sem régua própria segue *Todos os dias*. A régua herdada aparece apagada, só para consulta, com os botões **Criar régua própria copiando…** e **Criar vazia**. Soltar uma playlist ou item nela também cria a régua própria, copiando a herdada.
  - **↻ Repetir nos dias úteis:** copia a régua aberta para segunda a sexta de uma vez. **Copiar para…** escolhe os dias, com atalhos *Dias úteis* e *Fim de semana*. Antes de substituir, o painel avisa quais dias já têm programação própria.
  - **Remover régua própria:** o dia volta a seguir o nível de cima.
  - Os dias com régua própria ficam marcados com um ponto laranja no seletor.
- **Aba Calendário:** o mês inteiro, com a régua que vale em cada dia pela cor da borda (cinza *Todos os dias*, azul *dia da semana*, laranja *exceção*). Cada dia mostra o feriado nacional (BrasilAPI), uma faixa de 24 h com os blocos e as playlists agendadas. Ao clicar num dia, o painel ao lado mostra o motivo da régua escolhida e a lista de horários. Dali dá para:
  - **criar exceção para o dia**, que começa como cópia da régua em vigor e abre na Programação;
  - **exibir uma playlist o dia todo**;
  - **remover a exceção**;
  - abrir a régua do dia da semana ou a de *Todos os dias*.
- **Ordem de decisão da TV:** 1) exceção da data; 2) régua do dia da semana; 3) *Todos os dias*. Dentro da régua escolhida valem as regras de antes: item avulso > playlist > **Playlist padrão** nos horários vazios. A régua é escolhida inteira. Uma régua própria vazia também vale e deixa o dia todo na Playlist padrão, o que serve, por exemplo, para um feriado.
- O topo do painel ("No ar") mostra a régua de hoje quando ela não é *Todos os dias*. `/api/player/state` ganhou o campo `ruler`.
- Cada playlist tem uma cor própria na biblioteca, na timeline e no calendário.
- **📣 Avisos por data** (painel do dia no Calendário → *Adicionar aviso para este dia*): o formulário de item abre só com os tipos que fazem sentido.
  - **Mensagem:** já vem com título e texto da data ("Hoje é Dia do Professor" + o texto da lista) e um degradê na cor do tipo de data.
  - **Imagem:** a busca na web abre sozinha, pesquisando pelo nome da data.
  - **Contador:** contagem regressiva até o dia, começando 7 dias antes por padrão.
  - **Hoje é dia:** só em dia com feriado ou data comemorativa.
  - Escolha o assunto (feriado, data da lista ou outro), **quantos dias antes** começa a aparecer, **o dia todo ou só no horário de serviço** e **repetir todo ano**.
  - O aviso anual acompanha a data móvel: Carnaval, Páscoa e Corpus Christi pela BrasilAPI, Dia das Mães pela lista. Num feriado de dois dias, ele segue o mesmo dia (o 1º ou o 2º). 29/02 cai em 28/02 nos outros anos.
  - Na TV, o aviso é **intercalado**: entra no fim da rotação do que estiver no ar, sem mexer na programação. Isso vale também durante um item avulso agendado, que passa a alternar com os avisos do dia. Sem isso, uma programação feita só de itens avulsos nunca mostraria os avisos.
  - No calendário, o dia ganha o selo 📣 N, e o painel do dia lista os avisos ("faltam 5 dias") com editar e excluir.
  - Os avisos ficam na playlist reservada `avisos` ("Avisos por data"), com `config.notice = {date, days_before, yearly, anchor, hours, title}`. Essa playlist não aparece nas listas do painel e não pode ser excluída.
- O calendário mostra as **datas comemorativas da lista curada** de cada dia (📅). Quando a data da lista é o próprio feriado (ex.: Natal), ela não se repete: o texto dela aparece junto do feriado.
- **Zoom livre na linha do tempo da Programação** (no lugar dos 3 botões fixos):
  - Atalhos *Dia todo*, *Hora*, *30 min*, *15 min*, *5 min* e *1 min*, botões − e + e uma barra deslizante.
  - **Mouse:** Ctrl + roda em qualquer ponto da linha do tempo (o movimento de pinça do touchpad também funciona), ou só a roda sobre a faixa de horas. O zoom fica centrado no horário sob o mouse. Arrastar a faixa de horas rola para os lados.
  - A grade se ajusta sozinha ao zoom (marcas e encaixe dos blocos de 1, 5, 10, 15 ou 30 min; com o dia todo na tela, de hora em hora). O texto ao lado da barra mostra a grade atual.
  - O zoom escolhido fica guardado no navegador.
- **Logo da Alava no widget de notícias:** no cabeçalho, à esquerda do título, separada por um traço fino na cor de destaque. Usa o `assets/watermark.png` (branco, fundo transparente), que é a versão com melhor contraste no fundo azul-escuro e tem o mesmo tamanho do logo do clima e do trânsito. Pode ser desligada no item (*Mostrar a logo da Alava no cabeçalho*).
#### Banco de dados
- `schedule.scope`: régua de cada bloco. Pode ser `all`, `wd:1`…`wd:7` (1 = segunda, como `isoweekday()`) ou `date:AAAA-MM-DD`. Os blocos existentes viram `all` na primeira execução, então a programação atual continua igual.
- Tabela nova `rulers(scope, created_at)`, com as réguas próprias criadas. É ela que diferencia uma régua própria vazia de um dia sem régua.
- `GET /api/notices` (avisos). `/api/calendar` ganhou `dates`, `holiday_text` e `notices` em cada dia, e `/api/player/state` ganhou `notices`, os ids dos avisos intercalados agora.
- API: `GET/PUT/DELETE /api/schedule?scope=…` (sem `scope` continua sendo *Todos os dias*), `GET /api/schedule/rulers`, `POST /api/schedule/copy` e `GET /api/calendar?month=AAAA-MM`.
#### Corrigido
- O rodapé do painel mostrava "v0.6.1".
- A explicação "Como a TV decide o que exibir" agora cita os avisos do dia durante os itens avulsos.

### [0.10.0] — 2026-11-18
#### Adicionado
- **Mensagem com muito mais opções:**
  - Fundo em **cor sólida**, **degradê** (duas cores, quatro direções e 8 combinações prontas) ou **imagem**, com controle de escurecimento (0–85 %) para o texto continuar legível.
  - **Título** opcional acima do texto; o texto mantém as quebras de linha digitadas.
  - **Fonte** (padrão, serifada, destaque, manuscrita, máquina de escrever, todas do Windows e sem depender de internet), **alinhamento**, **negrito**, **sombra** e **animação de entrada** (aparecer suave, aproximar, subir).
  - **Prévia ao vivo** no formulário, em escala de uma TV 1920×1080, que atualiza enquanto você edita (`/view/message-preview`).
- **Buscar imagens na web** para o fundo da mensagem e para itens de imagem. A busca usa o **nome do item**, que é obrigatório antes de pesquisar. Com `PEXELS_API_KEY` no `.env`, usa o Pexels (fotos profissionais, chave gratuita); sem chave, o Openverse (sem cadastro, só licenças que permitem uso comercial e sem conteúdo sensível). A imagem escolhida é baixada para `data/uploads/`, então a TV mostra mesmo sem internet. O crédito do autor aparece discreto no canto inferior direito.
- `PEXELS_API_KEY` no `.env.example`.
- **Notícias (RSS)** (📰 Notícias): item próprio da playlist que mostra uma manchete por vez, com foto, fonte, "há X min", resumo e barra de tempo. Na próxima vez que o item entra, continua da manchete em que parou.
  - 7 fontes prontas, testadas em 18/11/2026: g1 Últimas, g1 Rio, g1 Economia, Agência Brasil, BBC News Brasil, ge e InfoMoney. Aceita qualquer outro feed RSS ou Atom. Padrão: BBC + g1 Economia, que no teste trouxeram bem menos notícia policial.
  - **Filtro de palavras** (cada palavra vale como início de palavra: "tortur" pega "tortura", "morta" não pega "imortal"), já preenchido nos itens novos com termos de crimes e tragédias. A lista é editável.
  - Listas de vídeos ("VÍDEOS: …") e chamadas "ao vivo" do g1 são ignoradas; "VÍDEO:" no singular só perde o prefixo.
  - Botão **Testar feeds** no formulário: mostra quantas manchetes passam pelo filtro, as 3 mais recentes e quais feeds falharam.
  - Cache de 10 min por feed e atualização em segundo plano junto com o clima, então a tela abre sem esperar a internet. Sem internet, mostra as últimas manchetes baixadas. Um feed fora do ar não derruba os outros.
- **Curiosidades e datas** ("Hoje é Dia de…"):
  - **Item 📅 Hoje é dia** para as playlists: mostra as datas comemorativas de hoje, o feriado do dia e "Amanhã é feriado" / "Faltam N dias para o feriado" (até 15 dias antes). Em dia sem nada, a TV pula o item.
  - **"Aparecer curiosidades durante o horário de serviço"** (Configurações): a TV intercala essa tela na playlist no ar, num horário (padrão 08:00–18:00), a cada N minutos (padrão 30) e por N segundos (padrão 15). Não interrompe item avulso agendado.
  - **Lista curada** com 66 datas (comemorações, profissões, saúde, datas do Rio como São Sebastião e São Jorge), em `conteudo/datas_comemorativas.txt`. A lista em uso fica em `data/datas_comemorativas.txt` e é editada no painel, com validação linha a linha e botão para restaurar a padrão. Atualizar o sistema não apaga as alterações. Aceita datas fixas (`DD/MM`), móveis (`2º domingo/05` para o Dia das Mães, `último sábado/03`) e por dia do ano (`dia 256`, o Dia do Programador, que cai em 12/09 nos anos bissextos).
  - **Feriados nacionais** da BrasilAPI, guardados em `data/feriados_AAAA.json` (depois de baixados, funcionam sem internet). Se a BrasilAPI estiver fora, tenta de novo só depois de 1 h, para não atrasar a TV. Quando a lista tem uma data com nome parecido no dia do feriado, só a da lista aparece; Carnaval de segunda não anuncia "amanhã é feriado" para a terça.
  - Não usa a Wikipedia "neste dia", que no teste trouxe o massacre de Jonestown como primeiro fato do dia.
  - Testar qualquer dia: `/view/today?d=AAAA-MM-DD`, ou o campo "Testar outro dia" nas Configurações.
- **Leitura em voz alta das mensagens (Piper, offline):**
  - Opção **🔊 Ler a mensagem em voz alta** no formulário da mensagem, com escolha de voz, velocidade (devagar, normal, rápida) e um texto próprio para leitura (ex.: "dezoito horas" em vez de "18h"). Sem ele, lê o título e o texto da tela. Botão **▶ Ouvir** para testar no painel.
  - O áudio é gerado no próprio computador pelo Piper (open source, sem internet e sem custo), com voz pt-BR, e fica guardado em `data/tts/`: o mesmo texto não é gerado de novo.
  - Instalação: **Configurações → Voz → Instalar voz** (acompanha o progresso no painel), pelo `instalar.bat` (novo passo opcional) ou por `python ferramentas/instalar_voz.py`. Vozes: faber (padrão), cadu e jeff. ~22 MB do programa + ~63 MB por voz, em `ferramentas/piper/` (fora do Git).
  - As vozes ficam fixadas na versão `v1.0.0` do repositório de vozes: as de 11/2026 foram retreinadas para o Piper 1.5, que não tem executável para Windows, e o executável de 2023 as recusa.
  - O Piper roda dentro da própria pasta e devolve o áudio cru, que o servidor grava como WAV. Assim funciona mesmo com acento no caminho (ex.: `C:\Users\Maurício\…`), onde o `piper.exe` quebra.
  - Sem a voz instalada, a mensagem aparece normalmente, só que sem som.

#### Alterado
- O texto da mensagem agora é exibido como texto puro. Antes, um `<b>` digitado era interpretado como HTML; agora aparece literalmente. Para páginas com HTML, use o widget **HTML local**.
- As cores das mensagens só aceitam o formato `#rrggbb`, para nenhum valor estranho ir direto para a página.

#### Segurança
- `/api/image-import` só baixa imagens que o próprio servidor devolveu numa busca da última hora, então não serve para baixar qualquer endereço. Também confere se a resposta é imagem e se tem até 15 MB.

### [0.9.0] — 2026-11-18
#### Adicionado
- **Widget de Contador Regressivo** (⏳ Contador): título, data e hora do evento, cores do fundo e do texto, segundos opcionais e texto exibido quando a hora chega (padrão "Chegou a hora!"). Mostra dias só enquanto faltar 1 dia ou mais. Com "Tirar da TV depois que a hora chegar", o player deixa de exibir o item sozinho. Tela em `/view/countdown/{id}`.
- **Widget de HTML local** (📄 HTML local): envio de um `.html` (página única) ou de um `.zip` com a página e seus arquivos. Cada envio ganha a pasta `data/html/<id>/`, servida em `/html/...`, então links relativos (CSS, imagens, scripts) funcionam. No `.zip`, a página inicial é o `index.html` (na raiz ou dentro de uma única pasta). O servidor recusa `.zip` inválido, sem página `.html`, com caminhos que saiam da pasta (`../`), com mais de 2.000 arquivos ou com mais de 300 MB descompactado.
- **Vídeo: opção "Repetir"** no cadastro e na edição. Ligada (padrão), o vídeo recomeça até completar a duração do item, como antes. Desligada, ele toca uma vez e a TV passa para o próximo item quando o vídeo acaba, e a duração vira o tempo máximo. O painel mostra o tempo do vídeo e o atalho "Usar N s como duração". Itens de vídeo que já existiam continuam repetindo.

#### Corrigido
- A pré-visualização de vídeo no painel não repetia: um vídeo de 10 s num item de 20 s parava e ficava com a tela congelada. Agora a prévia segue a opção "Repetir", igual à TV.
- No cadastro de item, enviar um arquivo e depois trocar o tipo (ex.: vídeo → HTML) fazia o item novo apontar para o arquivo errado. Agora o arquivo é descartado ao trocar de tipo.

#### Segurança
- A prévia de páginas HTML no painel roda isolada (sem `allow-same-origin`), para que um script da página enviada não consiga ler o login do painel salvo no navegador.

### [0.8.1] — 2026-11-18
#### Corrigido
- **Tela de clima mostrava garoa com sol forte.** O modelo padrão da Open-Meteo às vezes devolve garoa (códigos 51/53) com 0,1 mm, e a TV exibia "Garoa fraca" com animação de chuva. Agora, garoa abaixo de 0,2 mm aparece como "Parcialmente nublado". Chuva de verdade, pancadas e trovoadas continuam iguais, assim como a previsão de 7 dias e os alertas do INMET. O código original do modelo fica em `current.code_raw` no `/api/weather`, para conferência.

#### Adicionado (temporário)
- **Comparação de modelos de clima** em `data/wx_compare.csv`: a cada 9 min grava o "agora" do modelo padrão (`best_match`) e do ECMWF (`ecmwf_ifs025`), com temperatura, condição, chuva, nuvens e umidade. Abre direto no Excel. Serve para decidir, em 02/12/2026, se vale trocar de modelo. `WX_COMPARE=0` no `.env` desliga.

### [0.8.0] — 2026-11-18
#### Adicionado
- **Aviso instantâneo para o player (WebSocket).** O player mantém uma conexão aberta em `/ws/player` e o servidor manda o estado novo assim que alguém salva algo no painel ou a programação troca de bloco. Antes o player perguntava a cada 5 s, e uma mudança no painel demorava até 5 s para chegar à TV; agora chega em menos de 0,1 s.
- O servidor confere a programação a cada virada de minuto e avisa os players quando entra outro bloco, sem depender de alguém salvar.
- No terminal do servidor: `[push] player conectado/desconectado` com o número de players conectados; no do player: "Aviso instantâneo ligado/caiu".
- `websockets` em `requirements.txt` (já vinha junto com `uvicorn[standard]`; agora está explícito porque o player usa).

#### Alterado
- Se a conexão cair (servidor reiniciando ou de versão antiga), o player volta a consultar `GET /api/player/state` a cada 5 s e reconecta sozinho (espera 1 s, 2 s, 4 s… até 30 s entre tentativas). A rota HTTP continua igual.
- `server.py` e `player.py` passam para a versão 0.8.0.

### [0.7.0] — 2026-11-18
#### Adicionado
- **`instalar.bat`**: instalação no computador da TV com dois cliques. Confere Python (3.10+), Git e Chrome, instala as bibliotecas, cria o `.env` perguntando senha, porta e monitor da TV e oferece iniciar com o Windows. Pode ser rodado de novo sem perder o `.env` nem os dados.
- **`atualizar.bat`**: fecha servidor, player e o Chrome da TV, baixa a versão nova (`git pull`), atualiza as bibliotecas, mostra a versão e as novidades e reabre o sistema. Roda a partir de uma cópia em `%TEMP%`, porque o `git pull` pode trocar o próprio arquivo enquanto ele roda.
- **`startup.bat`**: cria ou remove o atalho na pasta Inicializar do Windows. O atalho abre o `iniciar_alava_vision.bat` minimizado, que sobe o servidor (playlists e programação) e depois o player.
- `ferramentas/configurar.py`: perguntas do `.env`. Recusa senha vazia, a do exemplo ou com espaço/#/aspas; avisa se a porta estiver em uso e sugere uma livre; lista os monitores na numeração do player.
- `ferramentas/parar_alava_vision.ps1`: fecha só os processos desta instalação. `-Simular` lista o que seria fechado, sem fechar.
- `.gitattributes`: `.bat` e `.ps1` sempre com quebra de linha do Windows, qualquer que seja a configuração do Git do computador.

#### Alterado
- `iniciar_*.bat` passam o caminho da pasta na linha de comando do servidor e do player, para o `atualizar.bat` reconhecer exatamente os processos do Alava Vision.

### [0.6.4] — 2026-11-18
#### Alterado
- **A porta do servidor agora vem só do `.env` (`PORT`).** `iniciar_alava_vision.bat`, `iniciar_servidor.bat` e `player.py` usavam 8080 fixo e ignoravam o `PORT` do `.env`. Para usar outra porta (ex.: no computador da TV, onde a 8080 já está ocupada), basta mudar `PORT=` no `.env`. Sem `PORT` no `.env`, continua 8080.
- `player.py --port` continua funcionando e tem prioridade sobre o `.env`.

### [0.6.3] — 2026-11-18
#### Adicionado
- `?inmet=off` no endereço da tela de clima simula o INMET fora do ar: os alertas somem e aparece o aviso "INMET indisponível". Funciona com a previsão real ou junto com os cenários `?demo=`.
- Dois atalhos novos em Configurações → Pré-visualizar tela de clima: "INMET indisponível" (previsão real) e "Tempestade + INMET fora".

### [0.6.2] — 2026-11-18
#### Adicionado
- **Aviso de INMET indisponível na tela de clima.** Quando o Instituto Nacional de Meteorologia está fora do ar ou inacessível, a tela exibe um card cinza discreto no painel de alertas com o texto "INMET indisponível — Alertas não carregados". Antes os alertas simplesmente sumiam sem nenhum indicativo.
- O JSON de clima (`/api/weather`) agora inclui o campo `inmet_status`: `"ok"` (INMET respondeu), `"unavailable"` (exceção ao tentar acessar) ou `"disabled"` (código IBGE não configurado nas configurações).

#### Corrigido
- Número de versão no cabeçalho de `server.py` estava marcado como 0.6.0 em vez de 0.6.1.

### [0.6.1] — 2026-11-17
#### Corrigido
- **A tela de clima demorava a virar noite.** O dado de dia/noite do Open-Meteo vem em blocos de 15 minutos e o servidor guarda a previsão por até 9, então a noite chegava até ~25 minutos depois do pôr do sol. Agora a tela decide pelo relógio, comparando com o nascer e o pôr do sol de hoje, e confere a cada 30 segundos, trocando o céu, o ícone e o texto na hora certa.
- Depois do pôr do sol, enquanto o dado ainda dizia "dia", o sol era desenhado num ponto fixo alto do céu.

#### Adicionado
- **Crepúsculo de 20 minutos** após o pôr do sol: o sol desce abaixo do horizonte e o céu passa de dourado para lilás e depois para o azul da noite, com estrelas e lua surgindo aos poucos. O amanhecer faz o caminho inverso nos 20 minutos antes do nascer do sol. Com tempo nublado ou chuvoso o céu só escurece, sem cores quentes.
- `?hora=HH:MM` no endereço da tela de clima simula outro horário no céu. Novos atalhos "Crepúsculo" e "Amanhecer" em Configurações → Pré-visualizar tela de clima.

### [0.6.0] — 2026-11-17
#### Alterado
- **A tela de clima abre pronta**, sem "--°" nem "Carregando previsão…". O servidor já envia a página com a previsão embutida (`/view/weather`), então ela é desenhada no mesmo instante, sem esperar rede.
- O servidor atualiza a previsão e os alertas do INMET **em segundo plano a cada 9 minutos**, então quem abre a tela nunca espera a internet. Se a internet cair, continua mostrando a última previsão boa.
- "Atualizado às" mostra a hora em que a previsão foi obtida, e não mais a hora em que a página abriu.
- Fonte Inter salva no projeto (`static/fonts/inter-latin.woff2`, licença OFL). A tela de clima não depende mais do Google Fonts.

### [0.5.0] — 2026-11-17
#### Alterado
- O logo da Alava aparece **somente nas telas de clima e trânsito**. Sites, imagens, vídeos e mensagens passam a ser exibidos sem o logo. Isso também resolve o logo da Alava sobreposto ao logo do Acessórias.
- O logo agora faz parte das próprias telas (`static/weather.html` e `/view/traffic`), em vez de ser injetado pelo player. A pré-visualização do painel mostra exatamente o que vai para a TV.
- A tela de trânsito ganhou uma faixa escura no topo com o logo Alava, "Trânsito agora · cidade" e relógio. O mapa fica abaixo da faixa, porque o canto superior esquerdo do Waze e do Google Maps já tem a busca do próprio mapa e o logo ficaria por cima dela.

#### Removido
- Opções do player `--no-watermark`, `--wm-opacity` e `--logo`.

### [0.4.0] — 2026-11-17
> Projeto agora versionado com Git. Ponto de restauração da 0.3.0: commit `acb3fda` na branch `main`.

#### Adicionado
- **Player sempre no monitor da TV** (`monitors.py`): o player lê os monitores do Windows e abre o Chrome em tela cheia no monitor 2 (padrão), qualquer que seja a resolução, a escala de DPI ou a posição das telas.
  - Numeração: 1 = principal; 2, 3… = demais, da esquerda para a direita. `python player.py --list-monitors` mostra a lista.
  - Configurável por `--monitor N` ou `PLAYER_MONITOR` no `.env`. `--monitor 0` mantém a posição manual antiga (`--screen-x/--screen-y`).
  - A cada 10 s o player confere a janela: se ela saiu da TV, volta para lá. Se a TV for desligada ou desconectada, a janela é minimizada para não cobrir o monitor principal e volta sozinha quando a TV reaparece.
- `iniciar_alava_vision.bat`: sobe o servidor, espera ele responder e abre o player na TV.
- Repositório Git com `.gitignore` (fora: `.env`, `data/`, backups, caches e perfis dos projetos antigos) e `.env.example`.

#### Alterado
- `iniciar_player.bat` não usa mais `--screen-x 1920` fixo, que só funcionava por coincidência em algumas disposições de tela.

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

> Meta: transformar o Sistema Unificado num sistema distribuído, com vários players na rede.
>
> Já entregue no Sistema Unificado (0.1.0 a 0.7.0): backend FastAPI com REST API, painel web
> com login (no lugar do app desktop Qt), player Chrome via CDP e conteúdo de vídeo.

### Planejado
- **Vários players na rede**: cadastro de cada TV no painel, com playlist e programação próprias
- **Usuários e permissões**: hoje existe uma senha única para o painel
- **Métricas em tempo real**: o que cada TV está exibindo e se está online
- **Conteúdo local fora do Chrome** (avaliar): o player usa só o Chrome; a parte em Qt prevista para conteúdo local ainda não existe

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
