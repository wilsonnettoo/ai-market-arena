---
name: arena-publicar
description: Execute e diagnostique o caminho de escrita do ciclo diário do AI Market Arena — gravar os artefatos do dia atomicamente, encadear no hash, carimbar no OpenTimestamps e commitar, sempre nessa ordem e nunca parcialmente. Use ao rodar o ciclo à mão, quando o cron diário falhar ou deixar de rodar, quando faltar um dia no histórico público, ao mexer em arena/audit/publish.py ou no workflow daily.yml, e para decidir entre publicar registro ou publicar OutageRecord. Inclui a tabela de diagnóstico de falha do publicador e as proibições do append-only.
---

# Skill: arena-publicar

Grave os artefatos do dia, encadeie no hash e carimbe — nessa ordem, de forma idempotente, e nunca pela metade. Dia sem publicação é `OutageRecord` encadeado, nunca silêncio.

## QUANDO USAR

- "rode o ciclo de hoje", "rode o ciclo do dia X"
- "o cron falhou", "o workflow ficou vermelho", "faltou um dia no histórico"
- vou mexer em `arena/audit/publish.py`, `arena/audit/chain.py`, `arena/cycle.py` ou `.github/workflows/daily.yml`
- "esse dia deveria publicar registro ou outage?"

## QUANDO NÃO USAR

- Para verificar trabalho antes de commitar → `arena-verificar`
- Para divergência entre contrato, Parquet e o verificador JS → `arena-drift`
- Para aprender o invariante antes de escrever → `arena-standards`

---

## PRINCÍPIOS

Antes de qualquer comando, três regras que governam todo o caminho de escrita:

1. **Idempotente.** Rerodar o dia D nunca duplica linha na cadeia nem reescreve registro. O ciclo devolve `already_published` e não faz nada.
2. **Nunca parcial.** Escrita atômica: arquivo temporário e `os.replace`. Processo interrompido no meio nunca deixa JSON pela metade encadeado.
3. **Nunca reordenado.** A ordem é única e não negociável.

---

## A ORDEM

```
artefatos do dia (atômicos) -> append na cadeia -> carimbo externo -> commit
```

Nunca ao contrário, nunca parcial. O motivo de cada posição:

- Os artefatos vêm primeiro porque a entrada da cadeia carrega o `sha256` dos bytes em disco — não há o que hashear antes de existir arquivo.
- O append vem antes do carimbo porque o carimbo é sobre o hash-raiz do dia; carimbar antes carimbaria o estado de ontem.
- O commit vem por último porque é o que torna tudo público, e nada deve se tornar público sem estar encadeado.

**O gate que aborta:** se `verify_chain` falhar, o ciclo não escreve nada. Carimbar uma cadeia quebrada carimba o defeito.

---

## PASSO 1 — RODAR O CICLO

```bash
uv run python -m arena.cli run-daily --date 2026-07-28
```

Interpretação da saída:

| Saída | Significado | Ação |
|---|---|---|
| `published (N previsoes)` | Sucesso | Siga para o passo 2 |
| `already_published (0 previsoes)` | O dia já existe. Idempotência funcionando. | Nada a fazer |
| `outage (0 previsoes)` | O sistema funcionou e registrou a falha | Leia o `reason`; não é bug do publicador |
| `ValidationError` / traceback | O ciclo abortou antes de escrever | Passo 4 |

Sem `--date`, usa a data de hoje em UTC. Atenção ao operar do Brasil: depois das 21h de Brasília a data UTC já virou.

---

## PASSO 2 — VERIFICAR ANTES DE CARIMBAR

```bash
uv run python -m arena.cli verify
```

Passa quando imprime `PASS: N entradas`. **Não prossiga se falhar.** Uma cadeia quebrada carimbada externamente registra permanentemente que ela estava quebrada.

---

## PASSO 3 — CARIMBAR E COMMITAR

```bash
ots stamp chain/CHAIN.jsonl
git add data/ chain/
git commit -m "data: ciclo de $(date -u +%F)"
git push
```

A atestação nasce incompleta, pendente de agregação. Alguns dias depois:

```bash
ots upgrade chain/CHAIN.jsonl.ots && git add chain/ && git commit -m "data: upgrade das atestacoes OTS"
```

Falha do calendário OpenTimestamps **não** deve impedir a publicação — o workflow usa `continue-on-error` de propósito. O carimbo é refeito no dia seguinte, e a cadeia protege a ordem interna de qualquer forma.

---

## PASSO 4 — DIAGNÓSTICO DE FALHA

| Padrão de erro | Causa provável | Ação |
|---|---|---|
| `NOT_A_SESSION` no outage | Feriado, meio-pregão ou fim de semana | Correto. Nada a corrigir. |
| `UNIVERSE_UNAVAILABLE` | URL ou cabeçalho do CSV da Invesco mudou | Verifique ao vivo, atualize a fixture, registre em `docs/DECISOES.md` (D17) |
| `DATA_UNAVAILABLE` | Provedor de barras fora do ar, ou credencial ausente | Confira `ALPACA_API_KEY_ID`; rerode o dia depois |
| `QUALITY_BLOCK` | Fiscal reprovou: preço não positivo, campo nulo, sessão divergente | Leia `data/quality/<dia>.json`. Não conserte o preço. |
| `EMPTY_GRID` | Menos de 61 sessões de histórico | Esperado nos primeiros dias. Colete histórico antes. |
| `ValidationError` do pydantic | Contrato mudou e o produtor não | `arena-drift` |
| `prev_hash não aponta` | Linha da cadeia reescrita, ou histórico reescrito por force-push | BLOQUEIA. Não se conserta com rebase. |
| Cron deixou de rodar sem erro | Workflow desabilitado por inatividade do repositório, ou segredo expirado | `gh run list --workflow=daily --limit 7` |

### O modo de falha que realmente machuca

Não é o job que fica vermelho — é o job que **para de rodar** e ninguém nota. Confira semanalmente:

```bash
gh run list --workflow=daily --limit 7
```

Devem aparecer cinco execuções por semana. Menos que isso, investigue antes de olhar qualquer outra coisa.

---

## PUBLICAR REGISTRO OU OUTAGE?

Regra única: **todo dia de pregão gera exatamente uma entrada na cadeia.** Se não deu para publicar a grade, publique `OutageRecord` com o `reason` e encadeie.

Um dia sem nenhuma entrada é indistinguível, para quem audita de fora, de uma decisão que foi omitida porque deu errado. É por isso que o silêncio é pior que a falha registrada — e é por isso que a falha registrada é conteúdo, não vergonha.

---

## PROIBIÇÕES

- Nunca escreva em `data/` ou `chain/` sem passar por `arena/audit/publish.py`
- Nunca edite arquivo já publicado em `data/forecasts/`, `data/quality/`, `data/universe/`, `data/outages/`
- Nunca reescreva, reordene ou remova linha de `chain/CHAIN.jsonl`
- Nunca `git push --force`, em nenhuma branch
- Nunca `git rebase` sobre commit já carimbado
- Nunca carimbe com o `verify` vermelho
- Nunca preencha um dia faltante com dado coletado hoje como se fosse de então — o buraco fica, e a explicação vai num `OutageRecord` novo

Se você quebrou um destes por acidente, **não tente esconder**. Registre um `OutageRecord` descrevendo o que aconteceu e abra entrada em `docs/DECISOES.md`. A correção por acréscimo é o mecanismo previsto; apagar não é.

---

## CHECKLIST

```
ANTES DE PUBLICAR
  [ ] arena-verificar níveis 1 a 5 verdes
  [ ] O dia é sessão de pregão? (ou o outage está correto)

DURANTE
  [ ] run-daily rodou e devolveu published | already_published | outage
  [ ] verify devolveu PASS ANTES do carimbo

DEPOIS
  [ ] ots stamp feito
  [ ] commit contém data/ e chain/ juntos, nunca um sem o outro
  [ ] gh run list mostra a execução
```

---

## CONTEXTO

A ordem existe porque cada passo depende do anterior de forma que não dá para inverter sem quebrar a garantia: o hash é dos bytes em disco, o carimbo é do hash, e o público é do carimbo. Um commit que traz `data/` sem a linha correspondente em `chain/` cria um arquivo publicado que a cadeia não conhece — e um verificador honesto vai reportar isso como arquivo não registrado, o que é indistinguível de inserção posterior.

## DECISÕES QUE GOVERNAM ESTA SKILL

D1 (o produto é o registro), D3 (repositório público desde o dia 1), D4 (formato T0), D5 (sem VPS — o cron do GitHub Actions é agendador e âncora de tempo). Ver `docs/DECISOES.md`.
