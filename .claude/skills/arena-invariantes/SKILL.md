---
name: arena-invariantes
description: Audite o código do AI Market Arena caçando violações dos invariantes duros — float em registro hasheado, datetime sem timezone, requisição de barras sem Adjustment.RAW, modelo pydantic sem strict, escrita em data/ ou chain/ fora de audit/publish.py, métrica recalculada fora de metrics/, e valor de segredo commitado. Use antes de abrir PR, ao revisar PR de outro assistente, quando o verificador JS acusar hash divergente, ou periodicamente para varrer o repositório inteiro. Detecta por AUSÊNCIA da chamada obrigatória, não só por presença do padrão errado. Modo padrão é somente-detectar; só corrige com pedido explícito.
---

# Skill: arena-invariantes

Varra o repositório caçando violações dos invariantes definidos em `arena-standards`, reporte em tabela e **não corrija nada** salvo pedido explícito. Detectar sempre; corrigir só sob ordem.

## QUANDO USAR

- "vou abrir PR", "revise o PR do Codex", "revise o PR do Antigravity"
- "o verificador JS diz que o hash não bate"
- "o teste de paridade Python/JS falhou"
- varredura periódica: uma vez por semana, ou depois de qualquer merge na zona restrita

## QUANDO NÃO USAR

- Para aprender a regra antes de escrever → `arena-standards`
- Para rodar os gates de verificação antes de afirmar sucesso → `arena-verificar`
- Para detectar divergência entre contrato, Parquet e o verificador JS → `arena-drift`

---

## O QUE É ACEITÁVEL

Declare isto antes de acusar, senão a auditoria gera falso positivo e é desligada na segunda semana.

| Padrão | Status | Por quê |
|---|---|---|
| `float` em `research/` | PERMITIDO | Código de pesquisa descartável; nada dali vai para registro hasheado. |
| `float` em `tests/` | PERMITIDO | Fixtures e asserções numéricas não são serializadas. |
| `float(...)` em cálculo intermediário nunca serializado | PERMITIDO | Só o valor que entra no registro precisa ser string. |
| `Decimal("0.0001")` | PERMITIDO | O literal está dentro de string; é a forma correta. |
| `datetime.now(timezone.utc)` | PERMITIDO | É o padrão exigido. |
| Escrita em `data/` dentro de `arena/storage/` e `arena/audit/` | PERMITIDO | São os únicos donos do caminho de escrita. |
| `252` em `arena/metrics/` | PERMITIDO | Dono único da anualização. |
| Nome de variável de ambiente (`ALPACA_API_KEY_ID`) | PERMITIDO | Nome sim, valor nunca. |

---

## BUSCA AUTOMATIZADA

Rode na raiz do repositório. Cada bloco traz a legenda de como interpretar a saída.

### 1. Float em registro hasheado (I1)

```bash
grep -nE '(^|[^."'"'"'0-9A-Za-z_])[0-9]+\.[0-9]+' \
  arena/canonical.py arena/contracts/*.py arena/forecast/*.py 2>/dev/null \
  | grep -v 'Decimal("' | grep -v '^\s*#' | grep -v 'version'
```

Qualquer linha na saída é candidata a violação. Confira se o número entra num campo de registro: se sim, BLOQUEIA.

```bash
grep -rn 'float(' arena/ --include='*.py' | grep -v '^arena/metrics/'
```

Cada ocorrência precisa de justificativa: o resultado é serializado? Se sim, BLOQUEIA.

### 2. Datetime sem timezone (I2)

```bash
grep -rnE 'datetime\.now\(\s*\)|datetime\.utcnow\(|date\.today\(\)' arena/ scripts/ --include='*.py'
```

Saída vazia é o esperado. Qualquer linha BLOQUEIA. `ruff` com a regra `DTZ` também pega, mas rode os dois — `ruff` não olha string formatada à mão.

```bash
grep -rn 'timedelta(days=' arena/ --include='*.py' | grep -v calendar_us
```

Contar dias corridos para achar pregão AVISA: use `arena.ingest.calendar_us`.

### 3. Ausência de Adjustment.RAW (I3)

```bash
grep -rl 'StockBarsRequest' arena/ --include='*.py' | xargs -r grep -L 'Adjustment.RAW'
```

**Detecção por ausência.** Todo arquivo listado usa `StockBarsRequest` e **não** menciona `Adjustment.RAW` — BLOQUEIA. Saída vazia é o esperado.

```bash
grep -rl 'StockBarsRequest' arena/ --include='*.py' | xargs -r grep -L 'asof'
```

Arquivo sem `asof` AVISA: sem ele, papel que trocou de símbolo aparece sob o nome de hoje em dado antigo.

### 4. Modelo pydantic sem strict (I5)

```bash
uv run python scripts/check_contracts.py
```

Passa quando imprime `PASS: N modelos conformes` e sai com 0. Linhas `AVISA` são
esperadas para exceção documentada; qualquer `BLOQUEIA` reprova.

**Por que script e não grep.** Duas tentativas anteriores falharam de formas instrutivas.
`grep -L 'strict=True'` não serve: ele lista arquivos que não contêm a string em lugar
algum, então um arquivo com um modelo correto e um errado passa limpo. Comparar contagens
de `ConfigDict(` contra `strict=True` também não serve — deu falso positivo na primeira
execução real, porque o docstring do módulo mencionava os dois flags e inflava a contagem.
Introspecção lê a configuração **efetiva** da classe, incluindo o que veio por herança, e é
imune a comentário e docstring.

O script também verifica duas coisas que nenhum grep alcança: campo tipado como `float`
em qualquer contrato, e `strict=False` por campo sem entrada correspondente em
`docs/DECISOES.md` — a exceção ao invariante I5 precisa ser decidida, nunca herdada.

Sem `strict`, pydantic coage `0.56` para `"0.56"` em silêncio. Sem `extra="forbid"`, campo
desconhecido é aceito calado, que é como um dialeto entra pela porta dos fundos.

### 5. Escrita fora do caminho autorizado (I4)

```bash
grep -rnE '\.write_text\(|\.write_bytes\(|to_parquet\(|open\([^)]*["'"'"']w' \
  arena/ --include='*.py' | grep -vE '^arena/(audit|storage)/'
```

Qualquer linha BLOQUEIA. Só `arena/audit/publish.py`, `arena/audit/chain.py` e `arena/storage/` escrevem. Escrita direta pula o encadeamento no hash.

```bash
grep -rn 'CHAIN.jsonl' arena/ scripts/ --include='*.py' | grep -v '^arena/audit/'
```

Referência a `CHAIN.jsonl` fora de `arena/audit/` AVISA — leitura pode ser legítima (verificador), escrita nunca.

### 6. Métrica recalculada fora do dono (I6)

```bash
grep -rniE 'sharpe|sortino|calmar|annualiz|\b252\b' arena/ --include='*.py' \
  | grep -v '^arena/metrics/'
```

Qualquer linha BLOQUEIA. Duas implementações de Sharpe divergem sem quebrar teste nenhum e o placar público fica errado em dezenas de pontos-base sem que ninguém saiba por quê.

### 7. Segredo commitado

```bash
grep -rniE '(api_key|api_secret|secret_key|password|passwd|token)\s*[:=]\s*["'"'"'][^"'"'"']{8,}' \
  . --include='*.py' --include='*.yml' --include='*.yaml' --include='*.md' --include='*.toml' \
  | grep -v '.env.example' | grep -v 'os.environ' | grep -v 'secrets\.'
```

Qualquer linha BLOQUEIA e exige rotação da credencial, não só remoção do arquivo. **O repositório é público desde o primeiro commit:** segredo commitado já está vazado no momento em que o push acontece.

### 8. Registro publicado editado (I4)

```bash
git log --diff-filter=M --name-only --pretty=format: -- data/ chain/ | sort -u | grep -v '^$'
```

Todo arquivo listado sofreu **modificação** depois de criado. Em `data/` e `chain/` isso BLOQUEIA sem exceção: append-only significa que arquivo publicado só nasce, nunca muda. Saída vazia é o esperado.

---

## RELATÓRIO FINAL

Reporte exatamente neste formato, ordenado por gravidade:

| Invariante | Arquivo | Linha | Valor encontrado | Ação necessária |
|---|---|---:|---|---|
| I1 | arena/contracts/records.py | 88 | `p_up=0.56` | Trocar por string `"0.5600"` |

Se nada foi encontrado, escreva a frase literal e nada mais:

```
AUDITORIA LIMPA — 8 verificações rodadas, nenhuma violação de invariante.
```

Não escreva "parece ok", "acho que está tudo certo" nem "provavelmente não há problemas". Ou você rodou as oito e a saída estava vazia, ou você não auditou.

---

## CHECKLIST

```
[ ] 1. Float em registro hasheado          (saída vazia esperada)
[ ] 2. Datetime sem timezone               (saída vazia esperada)
[ ] 3. Ausência de Adjustment.RAW          (saída vazia esperada)
[ ] 4. Modelo sem strict / extra=forbid    (saída vazia esperada)
[ ] 5. Escrita fora de audit/ e storage/   (saída vazia esperada)
[ ] 6. Métrica fora de metrics/            (saída vazia esperada)
[ ] 7. Segredo commitado                   (saída vazia esperada)
[ ] 8. Registro publicado modificado       (saída vazia esperada)
```

---

## CONTEXTO

Toda regra auditada aqui tem um par no repositório que a torna real: um teste que falha ou um job de CI que reprova. Invariante que existe só em markdown não protege registro hasheado — é o modo de falha que os planos de trava do CRM demonstram, onde nove gates estavam especificados em prosa e nada no sistema impedia nada.

Se você encontrar uma violação que **nenhum teste pega**, o achado real não é a violação: é a ausência do teste. Reporte os dois.

## DECISÕES QUE GOVERNAM ESTA SKILL

D3 (repositório público — por isso a varredura de segredo), D7 (preço bruto), D8 (números como string). Os invariantes I1 a I6 são definidos em `arena-standards`; esta skill apenas os detecta.
