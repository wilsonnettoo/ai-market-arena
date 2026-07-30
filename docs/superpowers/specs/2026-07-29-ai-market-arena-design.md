# AI Market Arena — Design da Temporada Zero

**Data:** 29 de julho de 2026
**Autor:** Wilson Netto
**Status:** aguardando revisão
**Substitui operacionalmente:** `ai_market_arena_plano_mestre_2026-07-29.md` (o plano mestre continua sendo a referência de visão; este documento é o que se executa)

---

## 1. O que estamos construindo

Não é uma competição entre três IAs investidoras. É **um registro público, carimbado por terceiro e não-editável, de previsões e decisões publicadas antes do resultado**. As três filosofias de risco são o enredo que torna esse registro assistível.

O ativo é o histórico com prova de anterioridade. O placar é o trailer. O plano mestre já sabe disso na linha 1354 ("a principal vantagem competitiva não será a taxa de acerto"), mas o roadmap foi escrito como se o produto fosse a linha 50 ("quem ganhou mais"). Este documento corrige a inversão.

Consequência prática que ordena todo o resto: **o subsistema de maior valor é o mais barato de construir e o mais caro de adiar.** Cadeia de hash e âncora externa custam meio dia; registro não coletado não existe, e anterioridade não pode ser atestada retroativamente.

### O que o projeto não promete

Que a IA prevê o futuro; que existe taxa de acerto garantida; que o sistema supera o Nasdaq; que alguém deve copiar operações; que paper trading representa o mercado real. O resultado nulo — os agentes não terem habilidade mensurável — é o desfecho mais provável e será publicado com o mesmo destaque de um resultado positivo. Isso está declarado no manifesto antes da primeira previsão existir.

---

## 2. Restrições travadas

| Restrição | Valor | Origem |
|---|---|---|
| Tempo do autor | 8 h/semana → 1,0 a 1,5 dia-pessoa/semana | decisão do Wilson |
| Custo incremental | teto duro US$ 80/mês, média-alvo ~US$ 25 | decisão do Wilson |
| Publicação | repositório público desde o dia 1, zero vídeos até haver histórico | decisão do Wilson (linha 1233 do plano mestre apagada) |
| Formato T0 | tudo em claro menos `entry_limit`, `stop` e `target`, revelados sob hash no fechamento do horizonte | decisão delegada, escolhida aqui |
| Universo | Nasdaq-100 + QQQ. Sem cripto, sem alavancagem, sem opções, sem venda a descoberto | plano mestre |

O gargalo **não é escrever código** — três assistentes de IA fazem isso. É o tempo do Wilson decidir, revisar e fazer merge. Todas as estimativas abaixo estão em dias-pessoa de alguém dirigindo três assistentes.

### Por que não existe VPS no ano 1

Repositório público torna GitHub Actions e Pages gratuitos e ilimitados. Um ciclo único diário pós-fechamento não precisa de uptime. Eliminar o servidor não economiza dólares — economiza **horas de manutenção**, que é o recurso escasso. Servidor custa horas antes de custar dinheiro.

---

## 3. Estratégia: Carimbo Antes do Cérebro

**Tese em três frases.** Põe no ar já na semana 1 a única coisa que o projeto realmente vende — um registro público, hasheado e ancorado — e começa a acumular evidência estatística na semana 4, com previsões determinísticas e zero LLM. Os três agentes de IA entram no mês 7, quando o encanamento já tem meses de histórico auditado e gêmeos determinísticos servindo de comparador honesto. O estado terminal desenhado não é a morte: se o autor sumir, o sistema continua publicando sozinho.

**Por que esta e não as outras.** Três alternativas foram avaliadas e descartadas:

- *O Cofre e as Três Vozes* (agentes no ar na semana 18, canal no mês 6) pede 56 dias-pessoa e não cabe em 52. Fica sem comparador até o mês 10, o que a impede de responder "o LLM adiciona algo além do pré-filtro?".
- *Cartório Primeiro* (só previsões probabilísticas, sem carteira) tem o ativo científico mais forte — cerca de 15 mil previsões resolvidas por ano — mas joga fora a carteira inteira, e com ela morre "Três IAs na Bolsa" como produto editorial.
- *Carimbo Antes do Palco* (zero vídeos no ano 1) maximiza o histórico, mas é a estratégia com maior risco de abandono: meses sem nenhum retorno externo.

A vencedora consegue a potência estatística da terceira (grade de previsões desde a semana 4) **e** a carteira da primeira (mês 7), pagando com a paciência da segunda.

### A ordenação que resolve dois problemas de uma vez

Minimizar risco de abandono e minimizar tempo até significância estatística apontam para a mesma sequência: publicar cedo algo burro que acumula amostra, e adiar o que é caro e não depende de calendário. É por isso que esta é a única sequência internamente consistente.

---

## 4. Sequência de marcos

Total planejado: **~44 dias-pessoa**. Disponível no pior cenário (1,0 dia-pessoa/semana × 52): 52. Folga: ~15%. A folga não tem entrega prometida — reserva com entrega prometida é folga fictícia.

| # | Marco | Semanas | Dias-pessoa | Artefato público |
|---|---|---:|---:|---|
| M0 | Selo Gênese | 1 | 1,5 | Repo público com regras carimbadas antes de existir qualquer resultado |
| M1 | Gate de Dispersão | 2–4 | 2,0 | Relatório: as três personas são realmente três? |
| M2 | O Pulso | 4–8 | 3,5 | Grade diária de previsões determinísticas + cadeia de hash, atualizada sozinha |
| M3 | Verificador público | 8–10 | 1,5 | OpenTimestamps + verificador em JS no navegador do visitante |
| M4 | Núcleo de carteira | 10–18 | 6,0 | Ledger, ordens, fills, risco — com 3 baselines determinísticos rodando |
| M5 | Fiscal + 2º conector | 18–22 | 3,0 | Selo "duas fontes independentes concordam" em cada preço |
| M6 | Gateway de LLM | 22–26 | 3,0 | Contrato público de modelo, teto e política de fail-closed |
| M7 | **Os três agentes** | 26–34 | 6,0 | Seis carteiras no painel: 3 de LLM contra 3 determinísticas |
| M8 | Placar de calibração | 34–38 | 3,0 | Brier, curva de confiabilidade e intervalo de confiança honesto |
| M9 | Primeiro vídeo | 38–42 | 3,0 | ~4.500 previsões resolvidas, verificador rodando ao vivo |
| M10 | Red Team em CI | 42–46 | 1,5 | "Tentei fraudar meu próprio cartório e aqui está o que quebrou" |
| M∞ | Operação contínua | 8–52 | 10,0 | A série ininterrupta em si |

**Ordem de corte se a velocidade real ficar em 1,0 dia-pessoa/semana:** cai M10, depois M8 escorrega para o ano 2, depois M9 vira post escrito em vez de vídeo. M0 a M7 são inegociáveis — são o produto.

**Escopo do primeiro plano de implementação.** Este documento é o mapa do ano 1 inteiro, e é grande demais para um único plano executável. O primeiro plano cobre **M0, M1 e M2** — semanas 1 a 8, 7 dias-pessoa — que juntos entregam o registro público carimbado, o gate que valida a premissa das três personas, e a grade de previsões acumulando amostra. Cada marco seguinte ganha seu próprio ciclo de plano quando o anterior fechar; planejar M4 hoje é planejar contra uma velocidade real que ainda não foi medida.

### M0 — Selo Gênese (semana 1)

Repositório público no ar no dia 7 contendo:

- `MANIFESTO.md` — a pergunta que o projeto responde, a métrica-manchete, os critérios de fracasso pré-declarados, e a cláusula de que **resultado nulo será publicado com o mesmo destaque** do positivo.
- `policy/personas-v1.yaml` — os limites das três personas, congelados.
- `docs/FILL_SPEC.v1.md` — como uma ordem vira execução, escrito antes de existir o simulador. Preenchimento é função pura de (ordem, barras posteriores); congelar o spec agora permite implementar o Ledger depois sem custar calendário.
- `contracts/*.json` — JSON Schema dos contratos congelados.
- `chain/000-genesis.json` — SHA-256 canônico de cada arquivo, encadeado.
- Atestação OpenTimestamps commitada ao lado.
- Branch protection: histórico linear, force-push bloqueado inclusive para admin, commits assinados por GPG.

Zero decisões, zero código de trading, zero vídeo — e mesmo assim já é a prova que ninguém consegue fabricar depois. É o artefato de maior razão valor/esforço do projeto inteiro.

**M0 é também o velocímetro.** Se não estiver no ar até a semana 5, a velocidade real é menor que a estimada e todo o resto do plano é reescalado imediatamente — não no mês 6, quando já custou vinte dias-pessoa descobrir.

### M1 — Gate de Dispersão (semanas 2–4)

Simula três carteiras long-only **aleatórias** do Nasdaq-100 com exatamente os limites das três personas, sobre dois anos de barras diárias. Mede a dispersão do retorno acumulado, a correlação par a par e contra o QQQ, e — o número que decide o projeto — **quanto da dispersão é explicada apenas pelo caixa obrigatório**.

O motivo: o Valentão fica no máximo 40% investido (5 posições × 8%), o Equilibrista tem 15% de caixa mínimo, e o Guardião pode comprar ETFs, ou seja, pode comprar o próprio benchmark. Se mais de 80% da dispersão vier do caixa, o vencedor de cada temporada é decidido pela direção do mercado cruzada com um arquivo de configuração, e a "comparação justa entre filosofias" é propaganda.

**Critério escrito antes de rodar.** Se reprovar, as personas são redesenhadas na semana 3 — igualando o caixa-alvo dos três e diferenciando por horizonte e por pool de candidatos — e não no mês 8, quando redesenhar significaria jogar fora meses de histórico.

### M2 — O Pulso (semanas 4–8)

A espinha inteira rodando sozinha, com o conteúdo mais burro possível e **zero LLM**:

- Storage append-only com `observed_at`, em SQLite + Parquet.
- Um conector de preço EOD em tier gratuito.
- Cadeia de hash: cada registro carrega o hash do anterior.
- Publicador em GitHub Actions com cron de pregão.
- **Grade diária de previsões probabilísticas**: P(ticker supera o QQQ em 5 pregões) para 25 nomes, por regra determinística de momentum. Custo zero, e a amostra começa a acumular na semana 4.
- Página estática em HTML puro no GitHub Pages, sem framework e sem build.
- **Arquivo point-in-time diário** — OHLCV bruto, ações corporativas, composição do QQQ do dia (mata viés de sobrevivência), calendário de earnings e macro. Arquivado mesmo sem uso: é o único item cujo custo de retrofit é infinito.

A frase que isso permite dizer no dia 28: *"esta página falou sobre amanhã ontem, todo dia, e nem eu consigo mudar o que ela disse."*

### M3 — Verificador público (semanas 8–10)

OpenTimestamps sobre o hash-raiz diário e um verificador em JavaScript que recalcula a cadeia inteira no navegador do visitante. Neste momento o artefato deixa de exigir confiança no Wilson e passa a ser verificável por um estranho — e é isso que se leva ao Hacker News, ao r/algotrading e às comunidades de forecasting e de avaliação de LLM.

Sem isso, "PostgreSQL imutável" e "commit público no GitHub" não provam nada: você é superusuário do banco, a data de autoria de um commit é um campo que o autor escolhe, e o histórico é reescrevível por force-push.

### M4 — Núcleo de carteira (semanas 10–18)

Ledger, máquina de estados de ordem, simulador de fills conforme o `FILL_SPEC` congelado no M0, e Gestor de Risco determinístico com limiares numéricos versionados. Rodando em cima: a estratégia burra "compra QQQ e segura" mais os três baselines determinísticos das filosofias.

O Ledger é o subsistema que o plano mestre inteiro esquece — o diagrama da seção 17 pula de EXECUÇÃO direto para AUDITORIA — e é o único que todos os outros consultam. A máquina de estados vai de `proposta` a `publicada`, `ativa`, `parcial`, `preenchida`, `stopada`, `expirada`, `encerrada`. Sem ela, uma ordem LIMIT nunca preenchida evapora do histórico, que é o mecanismo número um de inflação de track record no mundo inteiro. **A taxa de não-preenchimento é métrica de capa.**

### M5 — Fiscal + segundo conector (semanas 18–22)

O plano mestre pede "consistência entre fornecedores" como verificação do Fiscal (linha 306) e integra apenas uma fonte na Fase 1 (linha 1215). Com uma fonte só, a verificação mais importante do Fiscal é logicamente inexecutável e ele passa tudo reportando saúde perfeita. Duas fontes, tolerância de divergência declarada e regra de desempate escrita.

Preço é gravado **bruto + tabela separada de ações corporativas**, nunca só o ajustado — o parâmetro de ajuste vem ligado por padrão em vários fornecedores, então o erro acontece por omissão.

### M6 — Gateway de LLM (semanas 22–26)

Ponto de entrada único e auditável: cache por hash de prompt (prefixo estável **antes** de qualquer timestamp, senão o cache é 100% inútil), persistência de prompt renderizado, resposta bruta, `model_id` enviado **e** o campo `model` retornado, teto de custo diário com kill switch determinístico.

**Fail-closed.** Falha de modelo vira `NO_DECISION` com `reason`, que é estado válido, e nunca um buraco no registro. Fallback silencioso de provedor é **proibido** nos três decisores: uma decisão de modelo não declarado é fraude experimental.

### M7 — Os três agentes (semanas 26–34)

O LLM emite shortlist ranqueada com probabilidade e a tese em três frases. **Fórmula versionada — nunca o LLM — calcula `entry_limit`, `stop` (por ATR), `target` e tamanho da posição.** Uma tabela de proveniência por campo, congelada no repo, torna executável a regra que hoje só existe em prosa no plano mestre.

Divergência forçada por design, não por adjetivo no prompt: pré-filtro determinístico que torna os pools quase disjuntos (o Valentão vê só o quartil superior de momentum com liquidez mínima; o Guardião vê só nomes com fluxo de caixa livre positivo em oito trimestres), assimetria de informação (o Guardião não vê manchete de 24h nem momentum curto; o Valentão não vê DCF nem retorno sobre capital), e cadências distintas.

**Métrica de divergência interna publicada diariamente:** sobreposição de Jaccard entre as posições de cada par, correlação dos retornos, e percentual de dias em que discordaram sobre o mesmo nome com o mesmo insumo. Se a sobreposição der 70%, a manchete honesta é "as três filosofias são a mesma IA com adjetivos diferentes" — e publicar isso vale mais que qualquer placar. O plano mestre mede manada de IA no mercado externo e nunca a interna, apesar de "três filosofias incompatíveis" ser uma hipótese empírica jamais testada.

Os três decisores rodam no **mesmo modelo com o mesmo effort**, para que a divergência seja atribuível à filosofia e não ao modelo. Painel mostra seis carteiras: três de LLM contra três determinísticas.

### M8 — Placar de calibração (semanas 34–38)

Resolvedor determinístico, e métricas com baselines obrigatórios ao lado: climatologia, momentum 12-1, moeda justa, e o "otimista fixo em 0,55". Brier, log loss, curva de confiabilidade em 10 faixas, intervalo de confiança por bootstrap, e **decomposição de Murphy separando confiabilidade de resolução** — que é o que denuncia o modelo covarde que responde sempre 0,55, fica lindamente calibrado e não sabe nada.

Toda métrica publicada sai com intervalo de confiança e selo de suficiência amostral. Para distinguir 60% de acerto de uma moeda são necessárias cerca de 194 observações; 41 pregões de carteira dão ~45. A grade diária resolve isso: chega ao mês 12 com milhares de previsões resolvidas.

### M9 — Primeiro vídeo (semanas 38–42)

Gravação de tela, 12 a 18 minutos, corte de silêncio e nada mais. Roteiro gerado a partir do próprio JSON. A ordem importa: abre o repo ao vivo e roda o verificador na frente da câmera; mostra a curva de calibração e diz onde o sistema é mal calibrado; **mostra os erros antes dos acertos**; abre o extrato e mostra as ordens que expiraram sem preencher, explicando que é isso que todo backtest esconde; mostra o placar das seis carteiras; mostra o log de falhas.

**Cadência bimestral no ano 1.** Semanal custaria 4 a 6 horas por vídeo — mais da metade do orçamento semanal — e canibalizaria a manutenção do sistema.

---

## 5. Orçamento

| Período | Custo/mês | Composição |
|---|---:|---|
| Meses 1–6 | US$ 0–5 | GitHub Actions e Pages grátis em repo público; OpenTimestamps grátis; conector EOD em tier gratuito; domínio amortizado |
| Meses 7–12 | US$ 30–50 | 2º provedor de preço US$ 10–30; tokens de LLM US$ 20–25 com cache agressivo |
| **Média do ano 1** | **~US$ 25** | Teto duro US$ 80 com kill switch testado |

O kill switch corta as chamadas ao atingir o teto e faz os agentes publicarem `NO_DECISION` com `reason=LLM_BUDGET_EXCEEDED`. O registro continua, a conta não estoura.

**Custo que o plano mestre não orçava:** as assinaturas dos três assistentes de codificação. Elas são custo afundado aqui, mas precisam aparecer no orçamento declarado como "construção + operação", senão o critério de interrupção da linha 1290 será avaliado olhando o número errado.

---

## 6. Arquitetura e fronteiras de módulo

```
arena/
  contracts/    Pydantic + JSON Schema + fixtures douradas      [ZONA RESTRITA]
  storage/      store bitemporal, arquivo bruto, as_of(), migrations
  ingest/       conectores: preço EOD, EDGAR/XBRL, FRED, calendários, holdings do QQQ
  quality/      Fiscal de Dados — funções puras -> DataQualityReport
  ledger/       posições, caixa, ações corporativas, máquina de estados de ordem
  execution/    simulador de fills conforme FILL_SPEC
  risk/         Gestor de Risco determinístico                  [ZONA RESTRITA]
  metrics/      Sharpe, Brier, calibração, atribuição           [ZONA RESTRITA]
  llm/          gateway: cache por hash, registro bruto, teto de custo
  agents/       personas; prompts/ é propriedade editorial      [ZONA RESTRITA]
  audit/        log append-only, hash chain, publicador, âncora externa
  cycle/        daily_cycle puro: (dados_as_of, política, versão) -> decisões
apps/
  panel/        site estático que lê SÓ os JSON publicados
  content/      roteiro/render — nunca importa dos pacotes de trading
policy/         risk_limits.yaml, personas.yaml (versionados e hasheados)
docs/           DECISOES.md (ADRs append-only), FILL_SPEC.md, MANIFESTO.md
tests/fixtures/ dados dourados + corpus adversarial
```

**Regra de dependência unidirecional**, verificada por import-linter no CI:
`ingest → storage → quality → ledger → execution → risk → cycle → metrics → audit → apps`. Nada volta. `risk/` não pode importar de `ingest/`. `apps/content/` não pode importar nada de `arena/`.

**Regra de fronteira que resolve a sobreposição semântica:** o Fiscal **detecta**, o Gestor **decide**, o LLM **propõe**, a fórmula **dimensiona**, o Ledger **contabiliza**, o Auditor **carimba**. Materializada como tipo, não como combinado: `quality/` emite flags; `risk/` consome flags e aplica política.

**Invariante de segurança:** nenhum componente que fala com LLM possui credencial de corretora, escrita no banco operacional ou saída de rede arbitrária. Isso resolve prompt injection estruturalmente — injeção vira tese ruim, nunca ordem — em vez de por boa intenção.

### Stack

Python + SQLite/Parquet + GitHub Actions + HTML estático. **Sem** Postgres no ano 1, Redis, Airflow/Prefect, dbt, TimescaleDB, Grafana, FastAPI, Next.js dinâmico, QuantConnect/LEAN, VPS. O pipeline é um DAG linear de doze passos que roda uma vez por dia sobre ~25 mil linhas por ano. Cada peça cortada é uma coisa a menos para consertar às 6h da manhã.

---

## 7. Divisão de trabalho entre os três assistentes

**Modelo: monorepo com propriedade por fronteira de módulo — um pacote, um dono — precedido de uma semana zero serial.**

Dividir por fase deixa dois dos três ociosos esperando gates. Dividir por tipo de tarefa ("um arquiteta, outro implementa") cria handoff em cada tarefa e transforma o Wilson no barramento de contexto entre três ferramentas sem memória compartilhada.

### Semana zero é serial e inegociável

Dias 1 a 3: **somente Claude Code**, produzindo `contracts/`, `AGENTS.md`, `CODEOWNERS`, `policy/` com as chaves definidas, e o esqueleto de CI. Nenhum outro assistente abre antes desse merge.

O motivo é concreto: os dois únicos artefatos quase-formais do plano mestre já contêm inconsistência interna verificada. O JSON da linha 1011 usa `"regime": "risk_on_fragile"`, valor que não existe na taxonomia das linhas 270-279. A fórmula das linhas 790-800 usa 8 pesos para a lista de 10 critérios das linhas 775-786 — e como os 8 somam exatamente 100%, é omissão, não arredondamento. Três assistentes lendo esse documento em paralelo vão resolver essas ambiguidades de três formas diferentes, e ninguém vai notar até a integração. Paralelizar antes dos contratos não é arriscado: é matematicamente garantido produzir três dialetos.

### Atribuições a partir do dia 4

| Assistente | Subsistemas | Por quê |
|---|---|---|
| **Claude Code** | `contracts/`, `ledger/`, `execution/`, `risk/`, `metrics/`, `cycle/`, `audit/`, `agents/` (código, não prompts). Revisor dos PRs dos outros dois. | Invariantes que atravessam múltiplos arquivos e cuja corretude não é verificável olhando um arquivo por vez. Três implementações ligeiramente diferentes de Sharpe destroem a comparabilidade sem quebrar nenhum teste. |
| **Codex CLI** | `ingest/` (um conector por tarefa), `quality/` (funções puras, testável offline com fixtures corrompidas), `storage/`, `llm/`, corpus do Red Team, scripts operacionais | Todo item tem entrada e saída completamente especificadas pelo contrato e é verificável por teste local, sem depender de outro módulo em andamento. |
| **Antigravity** | `apps/panel/`, identidade visual dos três agentes, verificador público em JS, `apps/content/`, mapa do repositório | A única frente genuinamente desacoplada: consome apenas os JSON publicados, nunca o banco de trading. Zero conflito de merge. **Não começa antes do M2**, porque painel é consumidor. |

### Protocolo git

- `main` protegida desde o commit zero: force-push desabilitado, commits assinados. Não é higiene — o repositório é a prova de anterioridade do produto.
- Isolamento por `git worktree`, um por assistente, com prefixo de branch obrigatório (`feat/cc/*`, `feat/cx/*`, `feat/ag/*`).
- Hook de pre-commit lê `ARENA_AGENT=cc|cx|ag` e **rejeita** commit fora do escopo daquele assistente. CODEOWNERS sozinho só age no PR, tarde demais para impedir o "conserto de passagem".
- PRs abaixo de ~400 linhas. Rebase no início de toda sessão. **Um slot de merge por dia**, feito só pelo Wilson, na ordem das camadas. Nenhum assistente tem permissão de push em `main`.
- Zona de exclusão (`contracts/`, `risk/`, `metrics/`, `agents/prompts/`, `policy/`, `.github/`): só por PR do Claude Code, isolado, aprovado pelo Wilson.
- Mudança de contrato é PR isolado com bump de `schema_version`, migração das fixtures douradas e entrada em `docs/DECISOES.md`. O CI recusa diff em `contracts/` sem diff em `DECISOES.md`.
- **Reverter, não adaptar.** Quando um assistente implementar algo fora do contrato, a correção é reverter o código, não estender o contrato — é assim que os três dialetos voltam pela porta dos fundos com aparência de decisão de design.

### Gates de CI

Validação de toda saída contra os JSON Schemas com **rejeição, nunca coerção**; import-linter para a ordem de camadas; golden-file tests em `metrics/`; property-based tests em `risk/`; `contracts_version` do `AGENTS.md` igual à do pacote; gitleaks; corpus adversarial do Red Team falhando o deploy se a taxa de sucesso de ataque subir.

### O que só o Wilson decide

Aprovar todo diff de `agents/prompts/` e de `policy/` — mudar um prompt é mudar o decisor. Ser o único a fazer merge. Revisar pessoalmente todo PR que toque em `risk/`, `audit/` e `contracts/`. Aprovar manualmente cada publicação (estado `PENDING_HUMAN_REVIEW` obrigatório antes de publicar). Promover ou não Challenger a Champion. **Cortar escopo** — um assistente sempre aceita construir mais um módulo; nenhum dos três vai dizer "isso não deve existir". E arbitrar as contradições do plano mestre em vez de deixar cada assistente resolver a sua.

### Convenções canônicas inegociáveis (vão no `AGENTS.md`)

Tudo em UTC, converte só na apresentação. Preço sempre bruto mais tabela de ações corporativas. Anualização 252, retorno log ou simples declarado explicitamente. Biblioteca de calendário de mercado obrigatória — o descasamento de horário de verão entre EUA e Brasil é fonte garantida de bug de fronteira de dia para quem opera de Brasília. E a regra de parada: **se a decisão que você precisa tomar não está em `docs/DECISOES.md`, PARE e pergunte. Não invente.**

---

## 8. O que foi cortado do plano mestre

- **Liga Crypto inteira** (seções 7.2, 10.4, Fase 5). Removida do documento, não adiada — escopo adiado continua consumindo planejamento e ansiedade. Ela derruba de quebra a justificativa de servidor 24/7 da linha 1144, que se apoiava em cripto enquanto a linha 1258 proíbe cripto na temporada 1.
- **QuantConnect/LEAN como motor de backtest.** Obriga a escrever cada estratégia duas vezes, e um backtest que roda em motor diferente do de produção não valida a produção. O backtest passa a ser o próprio ciclo diário rodado sobre dados `as_of`.
- **Replay de crises com LLM como validação.** O modelo sabe o que aconteceu em outubro de 2008 e o vazamento está nos pesos — nenhum prompt o remove. Obter resultado favorável ali é literalmente a "seleção de exemplos favoráveis" que a linha 110 proíbe. Fica como conteúdo, com o rótulo "reconstituição — o modelo conhece o desfecho" na tela.
- **Fluxo de opções em tempo real e dados OPRA.** O dado mais caro do conjunto, e nada nas regras das três personas exige latência sub-minuto.
- **Gamma de dealers, private credit como pipeline, market depth, MOVE.** Quatro famílias sem fonte viável.
- **Redis, Prefect/Airflow, dbt, TimescaleDB, Grafana, Next.js dinâmico, FastAPI.**
- **Os 16 fatores da Sentinela e o Global Sentinel Risk Index como pipeline.** Sobra o calendário de earnings e macro — a única coisa que muda decisão de curto prazo — mais curva de juros, petróleo e DXY. El Niño, cibersegurança, iene e chips viram pauta de vídeo pesquisada à mão.
- **A fórmula de 8 pesos do motor de eventos**, aritmeticamente inconsistente com a própria lista de 10 critérios. Substituída por uma pergunta binária determinística que bloqueia entradas.
- **Os 10 regimes classificados por LLM.** Mantidos os nomes pelo valor narrativo, mas definidos por regra determinística sobre séries do FRED, com enum fechado, `indefinido` como default e reetiquetagem retroativa proibida por constraint de banco.
- **"Download dos dados" como dump de série OHLCV.** Resolve a restrição contratual de redistribuição. O painel publica derivados à vontade.
- **Assinatura paga do painel e relatório pago na temporada 1.** Cobrar por análise de ativos determinados é o que mais consolida o caráter profissional sob a Res. CVM 20 — muito mais que AdSense.
- **"O Cagão" em título, thumbnail, tags, nome de canal, descrição e nos primeiros 7 segundos de áudio.** "O Guardião" é o nome formal; a regra vira linter de conteúdo, não nota de estilo.

**Decisão de nomenclatura pendente:** "Valentão" em português significa quem intimida os fracos, não quem assume risco. O personagem pretendido é o afoito. Trocar agora custa zero; trocar depois de 40 vídeos e identidade visual pronta é rebranding completo.

---

## 9. Condição de desistência

Escrita agora, antes de começar, porque a racionalização da continuação é indefinida — que é exatamente o viés que o projeto se propõe a expor nos agentes. A decisão não é apagar o repositório: é **congelar o escopo publicamente e manter só o que o calendário já pagou** (modo museu — o sistema continua publicando sozinho).

**Porta 1, semana 5.** Se o M0 e o M2 não estiverem no ar, a velocidade real é menor que a estimada e o plano inteiro é reescalado.

**Porta 2, semana 4.** Se o gate de dispersão mostrar que mais de 80% da variância vem do nível de caixa e mais um dia-pessoa de redesenho não derrubar isso abaixo de 50%, "três IAs, três filosofias" é propaganda e o produto editorial não existe.

**Porta 3, semana 26.** Se o pipeline publicou em menos de 80% dos pregões desde o M2, o problema é operacional e não há produto sem série contínua. Um cartório com buracos não vale nada.

**Porta 4, contínua.** Se a manutenção passar de 0,5 dia-pessoa por semana durante dois meses seguidos, M8 a M10 caem inteiros.

---

## 10. Decisões

Registradas em **`docs/DECISOES.md`**, que é a fonte de verdade — append-only, numeração única, e o campo "Decisão" preenchível só pelo Wilson. Este documento não duplica o conteúdo; duplicar seria criar duas versões que divergem em silêncio.

As nove decisões já tomadas (D1 a D9) estão registradas lá com contexto e consequência, e cobrem o que esta spec estabelece: o produto é o registro e não o placar, capacidade e orçamento, repositório público desde o dia 1, formato de divulgação em T0, ausência de VPS, backtest no motor de produção, preço bruto, números como string em registro hasheado, e a remoção da Liga Crypto.

As oito pendentes (D10 a D17) são, em ordem de urgência: nome do agente agressivo (bloqueia `policy/personas.yaml` e a identidade visual); idioma e público-alvo, que é decisão jurídica e não editorial; autoria editorial e narração; consulta a advogado de mercado de capitais; página de posições pessoais do autor; exibição do `p_up` até o M7; e duas que só a execução revela — o feed que a conta Alpaca acessa e a fonte da composição do QQQ.

**Regra de parada para os três assistentes:** se a decisão necessária não está em `docs/DECISOES.md` como *Decidida*, parar e perguntar. O CI reprova qualquer PR que altere `arena/contracts/`, `arena/canonical.py` ou `policy/` sem diff correspondente naquele arquivo.

---

## 11. Critérios de aceitação da Temporada Zero

- Cadeia de hash íntegra e verificável por terceiro desde o commit gênese, sem um único dia faltando ou com `outage_record` publicado no mesmo dia.
- Nenhuma edição destrutiva de registro; correções apenas por append.
- Toda saída validada contra schema, com rejeição em caso de divergência.
- Taxa de não-preenchimento de ordens publicada como métrica de capa.
- Toda métrica publicada com intervalo de confiança e selo de suficiência amostral.
- Divergência interna entre os três agentes publicada diariamente.
- Nenhuma chave real de corretora acessível ao sistema em momento algum.
