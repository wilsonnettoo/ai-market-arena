---
name: arena-drift
description: Detecte divergência silenciosa entre as três representações do mesmo registro no AI Market Arena — os campos do contrato pydantic, as colunas gravadas em Parquet, e os campos que site/verify.js recomputa no navegador. Use ao adicionar ou renomear qualquer campo de contrato, ao mudar arena/canonical.py, quando o teste de paridade Python/JS falhar, quando o verificador público acusar hash divergente, e antes de bump de schema_version. Extrai as listas de cada lado, ordena e faz diff — divergência entre esses três lados é o modo de falha que destrói a credibilidade do projeto.
---

# Skill: arena-drift

Extraia a lista de campos de cada uma das três representações do registro, ordene, faça diff, e classifique cada divergência. Divergência aqui não gera erro visível — ela faz o verificador público acusar fraude onde não houve.

## QUANDO USAR

- adicionei, removi ou renomeei campo em `arena/contracts/`
- mexi em `arena/canonical.py` ou em `site/verify.js`
- `nivel-5-paridade-js` falhou
- alguém relatou que o botão "Verificar a cadeia" do painel diz FALHOU
- antes de bump de `schema_version`

## QUANDO NÃO USAR

- Para caçar padrão errado no código → `arena-invariantes`
- Para rodar os gates antes de afirmar sucesso → `arena-verificar`

---

## OS TRÊS LADOS

O mesmo registro existe em três formas, e as três precisam concordar:

| Lado | Onde vive | O que define |
|---|---|---|
| A — Contrato | `arena/contracts/records.py` | Os campos, os tipos, o que é obrigatório |
| B — Persistência | `data/*.parquet`, `data/**/*.json` | O que de fato foi gravado em disco |
| C — Verificador público | `site/verify.js` | A forma canônica que o navegador do visitante recomputa |

A→B divergindo perde dado em silêncio. **A→C divergindo quebra a prova**, que é o produto.

---

## PASSO 1 — EXTRAIR OS CAMPOS DO CONTRATO (lado A)

Use introspecção, não grep: grep erra em herança e em campo com anotação de várias linhas.

```bash
uv run python - <<'PY' | sort > /tmp/arena_A.txt
from arena.contracts import ForecastRecord, OutageRecord, DataQualityReport, UniverseSnapshot
for m in (ForecastRecord, OutageRecord, DataQualityReport, UniverseSnapshot):
    for nome in m.model_fields:
        print(f"{m.__name__}.{nome}")
PY
wc -l /tmp/arena_A.txt
```

---

## PASSO 2 — EXTRAIR O QUE FOI GRAVADO (lado B)

```bash
uv run python - <<'PY' | sort > /tmp/arena_B.txt
import json, glob
for caminho in sorted(glob.glob("data/forecasts/*.json"))[-1:]:
    registros = json.load(open(caminho))
    for k in registros[0]:
        print(f"ForecastRecord.{k}")
for tipo, sub in (("OutageRecord","outages"), ("DataQualityReport","quality"),
                  ("UniverseSnapshot","universe")):
    for caminho in sorted(glob.glob(f"data/{sub}/*.json"))[-1:]:
        for k in json.load(open(caminho)):
            print(f"{tipo}.{k}")
PY
diff /tmp/arena_A.txt /tmp/arena_B.txt
```

**Legenda da saída do diff.** Linha com `<` existe no contrato e **não** foi gravada. Linha com `>` foi gravada e **não** existe no contrato. Saída vazia é o esperado.

Se um tipo ainda não tem arquivo publicado (normal no início), ele não aparece no lado B — isso é ausência, não divergência. Compare só os tipos que já publicaram.

---

## PASSO 3 — CONFERIR A FORMA CANÔNICA (lado C)

Este é o passo que protege o produto. Não compara nomes de campo: compara **byte a byte** o resultado das duas implementações.

```bash
uv run python scripts/check_js_parity.py
```

Passa quando imprime `PASS: N casos, forma canonica identica em Python e JavaScript`.

Quando falhar, compare as quatro decisões de serialização diretamente:

```bash
echo "--- Python (arena/canonical.py) ---"
grep -nE 'sort_keys|separators|ensure_ascii|allow_nan' arena/canonical.py
echo "--- JavaScript (site/verify.js) ---"
grep -nE 'sort\(\)|JSON.stringify|Number.isInteger|join\(","\)' site/verify.js
```

As quatro decisões que precisam bater: chaves ordenadas, separadores sem espaço, UTF-8 literal sem escape ASCII, e nenhum número decimal. **`arena/canonical.py` é normativo — corrija o JavaScript, nunca o contrário.** A cadeia já publicada depende do Python.

---

## PASSO 4 — CONFERIR SE O TESTE DE PARIDADE COBRE O CAMPO NOVO

Detecção por ausência: o teste passa e mesmo assim não cobre nada do que você mudou.

```bash
grep -c "^    {" scripts/check_js_parity.py
grep -n "CASOS = \[" -A 20 scripts/check_js_parity.py
```

Se você adicionou um campo com característica nova — acento, caractere de controle, aninhamento mais profundo, lista de objetos — e nenhum caso do `CASOS` exercita essa característica, o nível 5 está verde por sorte. Acrescente um caso.

---

## CLASSIFICAÇÃO DA DIVERGÊNCIA

| Tipo | Sinal | Ação |
|---|---|---|
| **A — Crítica** | Divergência A↔C, ou `check_js_parity.py` falhando | BLOQUEIA. Nenhum commit, nenhum append na cadeia. Corrija o JS. |
| **B — Perda de dado** | Campo no contrato ausente do gravado (`<` no diff) | BLOQUEIA. O publicador não está serializando tudo. |
| **C — Esperada** | Tipo de registro que ainda não publicou nenhum arquivo | PERMITIDO. Não é drift, é ausência. Documente qual. |
| **D — Intencional** | Bump de `schema_version` com registros antigos no formato anterior | PERMITIDO. Registro antigo **não** é migrado: append-only. O leitor trata as duas versões. |

O tipo D é a única forma legítima de os três lados discordarem, e ela exige entrada em `docs/DECISOES.md` antes do merge — o CI reprova diff em `arena/contracts/` sem ela.

---

## PROIBIÇÕES

- Nunca migre registro já publicado para o novo schema. Append-only significa que o registro antigo fica no formato antigo, para sempre.
- Nunca "conserte" o Python para casar com o JavaScript. O Python é normativo.
- Nunca faça append na cadeia com o nível 5 vermelho.
- Nunca renomeie campo de contrato sem bump de `schema_version` — o verificador público de um visitante que abriu a página ontem passaria a acusar divergência.

---

## RELATÓRIO

```
DRIFT — <o que mudou>

Lado A (contrato):        N campos em 4 tipos
Lado B (gravado):         N campos, últimos arquivos de cada tipo
Lado C (paridade JS):     PASS | FAIL

A↔B: <vazio | lista com legenda < e >>
A↔C: <PASS | FAIL com os 4 pontos de serialização comparados>
Cobertura do teste de paridade para o campo novo: <sim | não, caso acrescentado>

Classificação: <A crítica | B perda | C esperada | D intencional>
```

Se estiver limpo, a frase literal:

```
SEM DRIFT — três lados concordam, paridade Python/JS verde.
```

---

## CHECKLIST

```
[ ] 1. Campos do contrato extraídos por introspecção
[ ] 2. Diff A↔B com legenda lida             (vazio esperado)
[ ] 3. check_js_parity.py                    (PASS)
[ ] 4. Teste de paridade cobre o campo novo  (caso acrescentado se necessário)
[ ] Se houve bump de schema_version: entrada em docs/DECISOES.md
```

---

## CONTEXTO

Um estranho abre o painel, clica em "Verificar a cadeia agora", e o JavaScript no navegador dele recomputa o hash de cada arquivo publicado. Se `site/verify.js` serializar de forma minimamente diferente de `arena/canonical.py`, o resultado é FALHOU — e o visitante conclui, corretamente pela evidência que tem, que o registro foi adulterado.

Esse é o pior modo de falha possível para este projeto: não perdemos um dado nem quebramos um teste, perdemos a única coisa que o projeto vende. E ele não dá erro em lugar nenhum até alguém de fora ver.

## DECISÕES QUE GOVERNAM ESTA SKILL

D1 (o produto é o registro), D3 (repositório público), D8 (números como string — a razão pela qual as duas implementações precisam concordar). Ver `docs/DECISOES.md`.
