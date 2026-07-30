# Decisões (ADRs)

**Append-only.** Nunca edite uma entrada existente; corrija com uma nova que referencie
a anterior. Isso espelha a regra do próprio produto: o registro não é reescrito.

**Só o Wilson preenche o campo "Decisão".** Os assistentes podem abrir uma entrada como
rascunho, com as opções e o trade-off escritos, e deixar o campo vazio.

**Regra de parada, válida para Claude Code, Codex e Antigravity:** se a decisão que você
precisa tomar não está aqui como *Decidida*, PARE e pergunte. Não invente.

O CI reprova qualquer PR que altere `arena/contracts/`, `arena/canonical.py` ou `policy/`
sem um diff correspondente neste arquivo.

---

## Decisões tomadas

### D1 — O produto é o registro, não o placar
**Data:** 2026-07-29 · **Status:** Decidida

**Contexto.** O plano mestre se descreve como uma competição entre três IAs investidoras,
mas a linha 1354 dele já admite que "a principal vantagem competitiva não será a taxa de
acerto". A análise confirmou: o ativo é o registro público carimbado de decisões
publicadas antes do resultado, e o placar é o que torna esse registro assistível.

**Decisão.** O produto é o registro com prova de anterioridade verificável por terceiros.
Toda priorização de escopo se resolve em favor dele. O placar é enredo.

**Consequência.** A cadeia de hash, o carimbo externo e a proteção do histórico vêm
antes de qualquer agente. O painel é consumidor, não produtor.

---

### D2 — Capacidade e orçamento
**Data:** 2026-07-29 · **Status:** Decidida

**Decisão.** 8 horas por semana do Wilson. Teto duro de US$ 80/mês de custo incremental,
com média-alvo de ~US$ 25. As assinaturas dos assistentes de codificação são custo
afundado, mas entram no orçamento declarado como "construção + operação".

**Consequência.** A 8h/semana o rendimento é de 1,0 a 1,5 dia-pessoa por semana, porque
o gargalo é decidir, revisar e fazer merge — não escrever código. Só fontes de dados
gratuitas ou baratas. Cadência de vídeo bimestral no ano 1; semanal custaria 4 a 6 horas
e canibalizaria a manutenção do sistema.

---

### D3 — Repositório público desde o dia 1
**Data:** 2026-07-29 · **Status:** Decidida

**Contexto.** A linha 1233 do plano mestre impunha "zero publicação pública" até o dia 91.
Na velocidade real, o dia 91 do plano cai em algum ponto de 2027, e o modo de morte mais
provável do projeto passa a ser o mês 5 com 70% construído e nada publicado.

**Decisão.** A linha 1233 está apagada. Repositório público, JSON diário e página estática
desde o início, rotulados "Temporada Zero — sistema em validação". Zero vídeos até haver
histórico.

**Consequência.** Os primeiros registros públicos vão mostrar erros, e a regra de
não-edição vale para eles também. Bugs viram o formato "Falha do sistema" que a linha 1057
do plano mestre já prevê.

---

### D4 — Formato de divulgação em T0
**Data:** 2026-07-29 · **Status:** Decidida

**Contexto.** O JSON da seção 15 do plano mestre publica ticker, ordem, limite, stop e
alvo — uma operação replicável na íntegra, em português, diariamente, com monetização
prevista. O plano reconhece na linha 118 que disclaimer não descaracteriza atividade
recorrente de análise, e depois resolve o assunto em uma frase. Registro imutável e
divulgação em claro do parâmetro executável são coisas separáveis.

**Decisão.** Em T0 vão em claro: timestamp, agente, ticker, decisão, horizonte,
confiança, regime e tese. `entry_limit`, `stop` e `target` vão sob hash e são revelados
no fechamento do horizonte.

**Consequência.** O gancho editorial sobrevive inteiro e a auditoria continua verificável
por terceiros, mas o parâmetro acionável nunca é público antes do fato. Exige uma
cerimônia nova de "abertura do envelope" — que é conteúdo, não overhead. Exige também
âncora de tempo externa e branch protection, porque "PostgreSQL imutável" e "commit no
GitHub" não provam anterioridade a ninguém.

---

### D5 — Sem VPS no ano 1
**Data:** 2026-07-29 · **Status:** Decidida

**Decisão.** Nenhum servidor. Repositório público torna GitHub Actions e Pages gratuitos e
ilimitados; o ciclo é único e roda após o fechamento.

**Consequência.** Isso não economiza dólares, economiza horas — servidor custa manutenção
antes de custar dinheiro, e manutenção é o recurso escasso. O argumento do plano mestre
para servidor 24/7 (linha 1144) se apoiava em cripto, que a linha 1258 proíbe na
temporada 1: o plano derrubava a própria exigência e não percebeu.

---

### D6 — Backtest no motor de produção, não no LEAN
**Data:** 2026-07-29 · **Status:** Decidida

**Decisão.** QuantConnect/LEAN sai como motor de backtest. O backtest é o próprio ciclo
diário rodado sobre dados `as_of`, e o replay histórico vira um parâmetro de data.
QuantConnect permanece apenas como candidato na comparação de *fornecedores* de dados.

**Consequência.** Evita escrever cada estratégia duas vezes. Um backtest que roda em
motor diferente do de produção não valida a produção, e mataria o gate de "histórico
reproduzível" pela raiz.

---

### D7 — Preço bruto, sempre
**Data:** 2026-07-29 · **Status:** Decidida

**Decisão.** Toda barra é gravada com `Adjustment.RAW`, mais tabela separada de ações
corporativas (que entra no M4 com o Ledger). Nenhum preço ajustado no registro.

**Consequência.** O parâmetro de ajuste é opcional na API do Alpaca, então o erro
aconteceria por omissão. Em M2, a resolução de previsão anula a observação (`void`) quando
detecta variação diária acima de 25% na janela — é isso que permite a M2 não precisar
ainda da tabela de ações corporativas.

---

### D8 — Números como string em registro hasheado
**Data:** 2026-07-29 · **Status:** Decidida

**Decisão.** Nenhum float dentro de registro hasheado. Preços e probabilidades viajam como
string. `arena/canonical.py` levanta `TypeError` se encontrar um float em qualquer
profundidade.

**Consequência.** Ponto flutuante não tem forma canônica reprodutível entre Python e
JavaScript, e o verificador que roda no navegador do visitante precisa recomputar
exatamente o mesmo hash. Um teste de paridade no CI falha se as duas implementações
divergirem — sem ele, elas divergiriam em silêncio e o verificador público passaria a
acusar fraude onde não houve.

---

### D9 — Liga Crypto removida do escopo
**Data:** 2026-07-29 · **Status:** Decidida

**Decisão.** Removida do documento, não adiada. Entra depois de um gate explícito de
decisão, nunca por calendário.

**Consequência.** Escopo adiado continua consumindo planejamento e ansiedade. A Liga
Crypto exigiria motor 24/7, janelas, monitoramento de funding e liquidações, políticas de
fim de semana e simulação de depeg — perto de 40% da complexidade operacional total, para
zero valor incremental na temporada 1.

---

## Decisões pendentes

### D10 — Nome do agente agressivo
**Status:** Pendente · **Bloqueia:** `policy/personas.yaml`, identidade visual, nome de arquivos

**Contexto.** "Valentão" em português significa quem intimida os fracos — *bully*. O
personagem pretendido é o afoito, quem assume risco. São coisas diferentes, e a segunda é
simpática enquanto a primeira não é. Decidir agora custa zero; depois de quarenta vídeos e
identidade visual pronta, é rebranding completo. O identificador `agressivo` está em uso
no código até isto ser resolvido.

**Opções.**

| Opção | Consequência |
|---|---|
| Manter "Valentão" | Zero trabalho agora. Carrega uma conotação de agressão contra pessoas que não é o personagem, e atrapalha patrocínio institucional. |
| "O Afoito" | Descreve exatamente o traço: age rápido, aceita errar. Palavra pouco usada, o que é bom para busca e memória. |
| "O Apostador" | Claro e memorável, mas associa o projeto a jogo de azar — ruim num projeto que vende rigor estatístico. |
| "O Impaciente" | Preciso e simpático; enfraquece um pouco o lado "assume risco". |

**Recomendação.** "O Afoito".

**Decisão:** _(pendente)_

---

### D11 — Idioma e público-alvo
**Status:** Pendente · **Bloqueia:** linguagem do painel, do manifesto e dos vídeos

**Contexto.** Esta é uma decisão jurídica, não editorial. É o direcionamento ao investidor
brasileiro que ancora a competência da CVM — não a existência de BDRs nem o fato de os
ativos serem americanos.

**Opções.**

| Opção | Consequência |
|---|---|
| Português, público brasileiro | Mercado que você conhece e onde a comunicação é natural. Traz o projeto para dentro do escopo da CVM, o que torna D4 e D13 mais importantes. |
| Inglês, público internacional | Reduz a exposição regulatória brasileira e amplia muito o público de *forecasting* e avaliação de LLM, que é onde o verificador de cadeia realmente ressoa. Custa fluência editorial e afasta a audiência natural. |
| Painel e repositório em inglês, vídeos em português | Separa o artefato técnico (que circula em Hacker News e comunidades de eval) do produto editorial. Mais trabalho de manutenção de duas superfícies. |

**Decisão:** _(pendente)_

---

### D12 — Autoria editorial e narração
**Status:** Pendente · **Bloqueia:** pipeline editorial (M9), estado `PENDING_HUMAN_REVIEW`

**Contexto.** Três consequências independentes se acumulam. A política de monetização do
YouTube trata como não monetizável persona de IA que se apresenta como especialista humano
dando orientação financeira — três agentes nomeados narrando compras em primeira pessoa é
o exemplo textual da política. As políticas de uso dos provedores de LLM exigem revisão por
humano qualificado antes da disseminação. E o plano mestre diagnostica na linha 88 que
conteúdo automatizado genérico pode não ser monetizado, e onze seções depois desenha
exatamente esse pipeline.

**Opções.**

| Opção | Consequência |
|---|---|
| Híbrido: Wilson narra o vídeo principal, TTS nos formatos curtos | Resolve os três problemas. Custa 45min a 1h por vídeo. Cobre a superfície de maior CPM com autoria humana. |
| Wilson narra tudo | Máxima segurança e retenção; maior custo de tempo. |
| 100% faceless com TTS, agentes em primeira pessoa | Menor esforço, risco alto de desmonetização e de violar política de provedor de LLM — o que derruba o sistema, não só o vídeo. |

**Recomendação.** Híbrido, com uma regra dura: **os agentes nunca falam em primeira pessoa
aconselhando.** A diferença entre "o Valentão diz: compre NVDA" e "o agente registrou uma
ordem simulada em NVDA; vejam por que o Advogado do Diabo discordou" é a diferença entre
desmonetizado e monetizável.

**Decisão:** _(pendente)_

---

### D13 — Consulta a advogado de mercado de capitais
**Status:** Pendente · **Bloqueia:** nada tecnicamente; é seguro de cauda

**Contexto.** A linha 1246 do plano mestre diz "revisar linguagem jurídica" sem nomear
ninguém nem estimar custo, e agenda isso para o dia 61-90 — depois de o schema e o formato
de divulgação já estarem construídos.

**Decisão:** _(pendente — orçar valor e prazo)_

---

### D14 — Página de posições pessoais do autor
**Status:** Pendente · **Bloqueia:** conteúdo do painel

**Contexto.** É o conflito de interesse mais provável de aparecer, e o capítulo 19 inteiro
do plano mestre nunca menciona o assunto. Se você tem NVDA na carteira pessoal e um agente
compra NVDA, alguém vai perguntar.

**Opções.** Página fixa declarando as posições pessoais em ativos do NDX/QQQ, atualizada a
cada mudança · Declaração de que não há posições pessoais nesses ativos, se for o caso ·
Silêncio (não recomendado: a pergunta vem de qualquer forma, e responder depois soa pior).

**Decisão:** _(pendente)_

---

### D15 — Exibição do `p_up` até o M7
**Status:** Pendente · **Bloqueia:** painel (M2, Task 19)

**Contexto.** Na regra `momentum-1.0.0`, `p_up` é **idêntico entre as três personas** — a
diferenciação por filosofia só entra no M7, com pré-filtro de candidatos e assimetria de
informação. Está declarado no manifesto, mas o painel mostraria três colunas com o mesmo
número por vários meses.

**Opções.** Uma coluna só até o M7, com nota explicando que as personas entram depois ·
Três colunas desde já, com aviso de que os números são idênticos por construção.

**Recomendação.** Uma coluna. Três colunas iguais sugerem três sinais onde existe um, e
isso contradiz o próprio produto.

**Decisão:** _(pendente)_

---

### D16 — Feed de dados do Alpaca
**Status:** Pendente até a execução · **Bloqueia:** `ALPACA_FEED`, horário do cron

**Contexto.** A resposta depende do que a conta gratuita efetivamente acessa, e só a
execução revela. O plano de M2 (Task 12, Step 6) traz o comando de verificação.

**A registrar.** Qual feed (`iex` ou `sip`), qual a defasagem, e se o ciclo pode rodar 30
minutos após o fechamento ou precisa esperar mais.

**Decisão:** _(pendente — preencher ao executar)_

---

### D20 — A métrica do gate de dispersão é concordância de ranking, não R²
**Data:** 2026-07-30 · **Status:** Decidida

**Contexto.** O plano especificava que o gate de dispersão reprovaria se mais de 80% da
**variância** dos retornos fosse explicada pelo nível investido, medido por R² de uma
regressão do retorno final contra a exposição. Medido empiricamente antes de rodar com dados
reais, esse R² se revelou **quase vazio**:

| Cenário | R² |
|---|---:|
| Volatilidade escala com o nível, ruído baixo | 0,079 |
| Volatilidade escala com o nível, ruído médio | 0,068 |
| Volatilidade idêntica, só o retorno médio escala | 0,040 |
| Perfeitamente determinístico (só o nível importa) | 0,9999 |

O R² só passa de 0,80 no caso determinístico. Em qualquer cenário realista fica entre 0,02 e
0,08, **e o gate aprovaria sempre** — o que é pior que não ter gate, porque dá falsa garantia.

A causa: o R² mede quanto o nível explica da variância **total**, e a variância **dentro** de
cada persona — qual sorteio de ações deu certo — domina o cálculo.

**Decisão.** A métrica passa a ser a **concordância de ranking**: em que fração das corridas
pareadas o ranking das três personas coincide com a ordem de exposição, ou com o exato
inverso dela. O inverso conta igual, porque também significa que o placar foi decidido pela
exposição, apenas num mercado de baixa. Limiar de reprovação: **80%**. Esperado sob puro
acaso: 2/3! = **33,3%**.

As corridas são **pareadas** — a corrida *i* usa a mesma semente nas três personas, como na
competição real, em que as três veem os mesmos pregões.

**Consequência.** O gate passou a ser informativo. Resultado com dados reais de 2024-07 a
2026-07, 2000 corridas: concordância de **61,3%**, aprovado. Um teste de regressão
(`test_metrica_antiga_por_r2_seria_vazia`) fixa o fato de que o R² não detectaria o que a
concordância detecta, para impedir volta silenciosa à métrica antiga.

---

### D19 — `strict=False` no campo `persona`, e só nele
**Data:** 2026-07-30 · **Status:** Decidida

**Contexto.** O invariante I5 exige `strict=True` em todo contrato: rejeição, nunca
coerção. Mas um teste de round-trip revelou que, com `strict` global, pydantic recusa a
string `"agressivo"` de volta para o membro de `Persona` — mesmo sendo `StrEnum`. A
consequência é grave e não óbvia: **o registro publicado deixa de ser legível pelo sistema
que o produziu.** O resolvedor de horizonte e o painel leem os JSON de `data/forecasts/`, e
os dois quebrariam.

Três alternativas foram testadas antes de decidir:

| Opção | Round-trip | Rejeita inválido | Custo |
|---|---|---|---|
| `Literal["agressivo", ...]` | funciona | sim | Perde iteração sobre as personas, `.value` e autocomplete |
| `Annotated[Persona, Field(strict=False)]` | funciona, devolve o membro real | sim | Uma exceção documentada, num campo |
| `use_enum_values=True` | funciona | sim | O campo passa a ser `str`; `r.persona is Persona.AGRESSIVO` fica falso |

**Decisão.** `Annotated[Persona, Field(strict=False)]`, aplicado **exclusivamente** ao
campo `persona` de `ForecastRecord`.

**Consequência.** Aceitar exatamente um dos três valores declarados no enum não é coerção
no sentido que I5 proíbe: valor fora do enum continua sendo rejeitado, e `strict` segue
valendo em todos os outros campos — confirmado por teste de que float em `p_up` ainda é
recusado. Qualquer outro campo que precise dessa exceção no futuro exige nova entrada aqui;
a exceção não é precedente geral.

O teste `test_round_trip_json_valida_de_volta_em_strict` fica como guarda permanente. Ele
não estava no plano original e é o que expôs o defeito.

---

### D18 — Ambiente real: Python 3.14.3 e pandas 3.0.5
**Data:** 2026-07-30 · **Status:** Decidida

**Contexto.** Os planos foram escritos supondo `pandas>=2.2`. O `uv sync` no ambiente do
Wilson resolveu para **pandas 3.0.5** e **Python 3.14.3**, com todos os wheels disponíveis
— não foi necessário fixar 3.13. Versões efetivas: pydantic 2.13.4, pyarrow 25.0.0,
exchange-calendars 4.13.2, ruff 0.16.0, pytest 9.1.1.

**Decisão.** Ficar em Python 3.14 com pandas 3.x. Não fixar versão anterior.

**Consequência.** Seis pontos do código planejado foram testados contra pandas 3.0.5 antes
de escrever o módulo:

| Ponto | Resultado |
|---|---|
| `DataFrame.map` (substituiu `applymap`) | funciona |
| `pivot(index=, columns=, values=)` | funciona |
| `pct_change()` sem `fill_method` | funciona |
| `pct_change()` em coluna de `Decimal` | funciona |
| `reindex` de coluna ausente | devolve `np.float64(nan)`, **não** `None` — o `.map` posterior converte para `None`, então o contrato do store se mantém |
| `Index.to_period("M")` | **falha** com `AttributeError` num `Index` comum de `datetime.date`; só existe em `DatetimeIndex` |

O último exigiu correção no plano de M1: `simular_carteira` passa a usar
`pd.DatetimeIndex(retornos.index).to_period("M")`. Sem isso o gate de dispersão quebraria
na primeira execução com dados reais.

---

### D17 — Fonte da composição do QQQ
**Status:** Pendente até a execução · **Bloqueia:** `arena/ingest/universe.py`

**Contexto.** O CSV de holdings da Invesco é fonte gratuita sem contrato: URL e cabeçalho
podem mudar sem aviso. O plano de M2 (Task 13, Step 6) traz a verificação ao vivo, e o
ciclo trata a falha como `OutageRecord` sem quebrar a cadeia.

**A registrar.** URL confirmada, nomes exatos das colunas, número de constituintes, e uma
fonte alternativa caso a primeira caia.

**Decisão:** _(pendente — preencher ao executar)_
