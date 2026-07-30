---
name: arena-standards
description: Padrões obrigatórios do AI Market Arena — carregue ANTES de escrever ou editar qualquer arquivo em arena/, policy/, scripts/ ou site/. Cobre os invariantes duros do projeto (UTC, Adjustment.RAW, nenhum float em registro hasheado, append-only, rejeição nunca coerção, anualização 252), o stack permitido e proibido, a ordem de dependência entre camadas e a propriedade por path entre Claude Code, Codex e Antigravity. É a ÚNICA dona dos invariantes: as outras skills arena-* referenciam esta, nunca reescrevem a regra.
---

# Skill: arena-standards

Aplique todos os padrões obrigatórios do AI Market Arena antes de criar ou editar qualquer arquivo de código. Esta skill é a fonte única dos invariantes; se outra skill discordar dela, esta vence e a outra é o bug.

## QUANDO USAR

- "vou criar um contrato / um conector / um módulo em `arena/`"
- "preciso gravar preço", "preciso serializar um registro", "preciso calcular hash"
- antes de qualquer PR que toque `arena/`, `policy/`, `scripts/` ou `site/`
- quando um assistente propõe estender um contrato para acomodar código já escrito

## QUANDO NÃO USAR

- Para verificar trabalho pronto antes de commitar → `arena-verificar`
- Para caçar violações em código existente → `arena-invariantes`
- Para o caminho de escrita do ciclo diário → `arena-publicar`

---

## PASSO 0 — REGRA DE PARADA

Antes de escrever qualquer linha, confira se a decisão necessária está em `docs/DECISOES.md` com **Status: Decidida**.

```bash
grep -A2 "^### D" docs/DECISOES.md | grep -B2 "Status:.*Decidida" | grep "^### D"
```

Se a decisão que você precisa não está lá como Decidida, **PARE e pergunte ao Wilson**. Não invente. Um assistente que decide formato de divulgação, fonte de verdade da carteira ou nome de persona às 23h coloca essa escolha no histórico imutável sem que ela tenha sido decidida.

---

## STACK & VERSÕES

| Camada | Tecnologia | Observação |
|---|---|---|
| Linguagem | Python 3.13 ou 3.14 | via `uv`; `uv python pin 3.13` se faltar wheel |
| Contratos | pydantic v2 | `ConfigDict(extra="forbid", frozen=True, strict=True)` |
| Dados | pandas + pyarrow | Parquet por sessão |
| Persistência | SQLite + Parquet | arquivos no repositório |
| Calendário | exchange-calendars | `XNYS` |
| Mercado | alpaca-py | `Adjustment.RAW` sempre explícito |
| Agendador | GitHub Actions (cron) | é também a âncora de tempo |
| Painel | HTML + JS puro | sem build, sem framework |
| Carimbo | opentimestamps-client | `ots stamp` sobre o hash-raiz |
| Lint | ruff | regra `DTZ` habilitada |

**NÃO EXISTE neste projeto:** Postgres, Redis, Airflow, Prefect, dbt, TimescaleDB, Grafana, FastAPI, Next.js, QuantConnect/LEAN, VPS. Se você sentiu falta de um deles, o desenho está errado — o pipeline é um DAG linear de doze passos que roda uma vez por dia sobre ~25 mil linhas por ano.

---

## OS INVARIANTES

### I1 — Nenhum float em registro hasheado

```python
# ERRADO — quebra a prova pública
ForecastRecord(p_up=0.56, reference_close_raw=174.20)

# CERTO — decimal viaja como string
ForecastRecord(p_up="0.5600", reference_close_raw="174.2000")
```

Ponto flutuante não tem forma canônica reprodutível entre Python e JavaScript. `arena/canonical.py` levanta `TypeError` se encontrar um float em qualquer profundidade. Float é legítimo em `research/` (descartável, não vai para hash) e em cálculo intermediário que nunca é serializado.

### I2 — Tudo em UTC, conversão só na apresentação

```python
# ERRADO — ruff DTZ reprova, e o carimbo fica ambíguo
datetime.now()  ;  datetime.utcnow()  ;  date.today()

# CERTO
datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
```

Nunca conte dias corridos para achar pregão; use `arena.ingest.calendar_us`. O horário de verão americano muda em data diferente do brasileiro, e isso é fonte garantida de bug de fronteira de dia.

### I3 — Preço sempre bruto

```python
# ERRADO — parâmetro é opcional na API, então o erro entra por omissão
StockBarsRequest(symbol_or_symbols=s, timeframe=TimeFrame.Day, start=a, end=b)

# CERTO
StockBarsRequest(..., adjustment=Adjustment.RAW, feed=_feed(), asof=asof)
```

Preço ajustado muda retroativamente a cada ação corporativa — não serve a registro auditável. Grave bruto mais tabela separada de ações corporativas. `asof` faz o mapeamento histórico de ticker: sem ele, papel que trocou de símbolo aparece sob o nome de hoje em dado antigo.

### I4 — Append-only

Registro publicado nunca é editado. Correção é registro novo. Isso vale para `data/`, `chain/CHAIN.jsonl` e `docs/DECISOES.md`.

### I5 — Rejeição, nunca coerção

```python
# ERRADO — pydantic sem strict coage 0.56 para "0.56" em silêncio
model_config = ConfigDict(extra="forbid")

# CERTO
model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
```

Valor inválido gera `OutageRecord` e o dia é registrado como falha. Nunca um valor consertado.

### I6 — Anualização 252

Retorno simples salvo declaração explícita em contrário. Uma segunda implementação de Sharpe destrói a comparabilidade sem quebrar teste nenhum — por isso `arena/metrics/` é dono único e nenhum outro módulo recalcula métrica.

---

## ORDEM DE DEPENDÊNCIA

```
ingest → storage → quality → forecast → cycle → audit → site
```

Nada volta. `arena/canonical.py` não importa nada de `arena/`. `risk/` não importa de `ingest/`. `apps/content/` não importa nada de `arena/`. Verificado por import-linter no CI.

**Fronteira semântica:** o Fiscal **detecta**, o Gestor **decide**, a fórmula **dimensiona**, o Ledger **contabiliza**, o Auditor **carimba**. `quality/` emite flags e não decide nada.

**Invariante de segurança:** nenhum componente que fala com LLM tem credencial de corretora, escrita no banco operacional ou saída de rede arbitrária. Isso resolve prompt injection por construção — injeção vira tese ruim, nunca ordem.

---

## PROPRIEDADE POR PATH

| Path | Dono | Zona |
|---|---|---|
| `arena/canonical.py`, `arena/contracts/`, `arena/audit/`, `arena/cycle.py` | Claude Code | restrita |
| `arena/risk/`, `arena/metrics/`, `arena/forecast/`, `policy/`, `.github/` | Claude Code | restrita |
| `arena/ingest/`, `arena/quality/`, `arena/storage/`, `arena/llm/` | Codex | livre |
| `site/`, `apps/` | Antigravity | livre |

Zona restrita muda só por PR isolado do Claude Code, aprovado pelo Wilson, com nada mais no mesmo PR. Prefixo de branch obrigatório: `feat/cc/*`, `feat/cx/*`, `feat/ag/*`.

---

## PROIBIÇÕES

Nunca execute, em nenhuma circunstância:

- `git push --force` em qualquer branch — o histórico é a prova de anterioridade
- reescrever ou reordenar linha de `chain/CHAIN.jsonl`
- editar arquivo já publicado em `data/forecasts/`, `data/quality/`, `data/universe/`, `data/outages/`
- `git rebase` sobre commit já carimbado pelo OpenTimestamps
- escrever em `data/` ou `chain/` sem passar por `arena/audit/publish.py`
- estender um contrato para acomodar código já escrito — reverta o código
- colocar valor de segredo em qualquer arquivo: o repositório é **público**. Só nome de variável de ambiente.
- usar credencial que não seja de paper trading

---

## ARMADILHAS DO PROJETO

| Situação | Regra |
|---|---|
| Verificador JS acusa hash diferente | Float ou chave fora do contrato entrou no registro. Cheque o tipo, não a formatação. |
| Teste de paridade falha só no CI | `sort_keys`, `separators` ou `ensure_ascii` divergiram entre Python e JS. Corrija o **JS**: `arena/canonical.py` é normativo. |
| Barra desaparece do Parquet | Confundiu data da sessão com data de ingestão. Toda linha carrega as duas. |
| Variação diária acima de 25% | Ação corporativa não processada. O papel vai para quarentena e a previsão vira `void`. Nunca conserte o preço. |
| Dia sem publicação | Publique `OutageRecord` e encadeie. Silêncio é indistinguível de decisão omitida. |
| `p_up` igual nas três personas | Correto em `momentum-1.0.0`. A diferenciação entra no M7. Está declarado no `MANIFESTO.md`. |
| Precisa rerodar o dia D | O ciclo é idempotente: devolve `already_published` e não duplica linha na cadeia. |

---

## CHECKLIST

```
ANTES DE ESCREVER
  [ ] A decisão está em docs/DECISOES.md como Decidida?
  [ ] O path que vou tocar é meu? (tabela de propriedade)
  [ ] Se for zona restrita: o PR é isolado?

ANTES DE COMMITAR
  [ ] uv run ruff check .            (exit 0)
  [ ] uv run pytest -q               (exit 0)
  [ ] Nenhum float em campo de registro hasheado
  [ ] Nenhum datetime sem timezone
  [ ] Adjustment.RAW explícito em toda requisição de barras
  [ ] Nenhum valor de segredo no diff
```

---

## CONTEXTO

Os invariantes não são preferência de estilo. O produto deste projeto é um registro público cuja integridade um estranho verifica sozinho, no navegador dele, recomputando o hash. Isso só funciona se as duas implementações da forma canônica — `arena/canonical.py` e `site/verify.js` — produzirem byte idêntico para a mesma entrada. Um float que entra num registro hasheado não gera erro visível: ele faz o verificador público acusar fraude onde não houve, que é o pior modo de falha possível para um projeto que vende auditabilidade.

## DECISÕES QUE GOVERNAM ESTA SKILL

D1 (o produto é o registro), D2 (8h/semana e US$80/mês), D3 (repositório público desde o dia 1), D4 (formato T0), D5 (sem VPS), D7 (preço bruto), D8 (números como string). Ver `docs/DECISOES.md`.
