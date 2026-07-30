---
name: arena-verificar
description: Rode os seis níveis de verificação do AI Market Arena antes de afirmar que qualquer coisa está pronta, funcionando, corrigida ou passando — e antes de commitar, abrir PR ou mergear. Cada nível é um comando com exit code e saída esperada, ordenados do mais barato ao mais caro (ruff, pytest, invariantes, cadeia de hash, paridade Python/JS, ciclo real). Use também quando for tentado a escrever "deveria funcionar", "parece ok" ou "provavelmente está certo", e sempre que estiver a ponto de aceitar o relatório de outro assistente como evidência.
---

# Skill: arena-verificar

Rode os seis níveis, leia o exit code de cada um e só então afirme qualquer coisa. Pular um nível e afirmar sucesso não é otimizar tempo: é mentir.

## QUANDO USAR

- "está pronto", "corrigi", "funcionou", "os testes passam" — antes de escrever qualquer uma dessas frases
- antes de `git commit`, de abrir PR e antes de mergear
- quando o Codex ou o Antigravity reportar que a parte deles está pronta
- quando o ciclo diário falhar e você achar que sabe o motivo

## QUANDO NÃO USAR

- Para aprender a regra antes de escrever → `arena-standards`
- Para varrer o repositório caçando violação → `arena-invariantes` (é o nível 3 daqui)
- Para o caminho de escrita do ciclo → `arena-publicar`

---

## OS SEIS NÍVEIS

Ordenados por custo. Rode do 1 ao 6. Um nível que falha interrompe a sequência — não siga para o próximo "para ver se também quebra".

| Nível | Nome do job de CI | Comando | Passa quando |
|---|---|---|---|
| 1 | `nivel-1-lint` | `uv run ruff check .` | exit 0, nenhuma linha de saída |
| 2 | `nivel-2-testes` | `uv run pytest -q` | exit 0, nenhum `F` nem `E` |
| 3 | `nivel-3-invariantes` | os 8 greps de `arena-invariantes` | toda saída vazia |
| 4 | `nivel-4-cadeia` | `uv run python scripts/verify_chain.py` | exit 0 e imprime `PASS:` |
| 5 | `nivel-5-paridade-js` | `uv run python scripts/check_js_parity.py` | exit 0 e imprime `PASS:` |
| 6 | `nivel-6-ciclo-real` | `uv run python -m arena.cli run-daily --date <sessão>` | imprime `published` ou `already_published` |

O nome do job de CI é igual ao nome do nível de propósito: o check vermelho no PR diz sozinho qual nível caiu, sem abrir log.

### Sequência completa

```bash
uv run ruff check . \
  && uv run pytest -q \
  && uv run python scripts/verify_chain.py \
  && uv run python scripts/check_js_parity.py \
  && echo "NIVEIS 1,2,4,5 OK — rode o 3 (arena-invariantes) e o 6 separadamente"
```

O `&&` é deliberado: a sequência para no primeiro que falhar, e o exit code final é do que falhou.

---

## O QUE PROVA O QUÊ

Antes de afirmar, confira nesta tabela qual artefato a afirmação exige. A coluna da direita lista o que **parece** prova e não é.

| Afirmação | Requer | Não é suficiente |
|---|---|---|
| "Os testes passam" | `uv run pytest -q` com exit 0, saída colada | "escrevi os testes"; "rodei antes de mudar" |
| "A cadeia está íntegra" | `verify_chain.py` do gênese ao último registro, exit 0 | "o publicador não deu erro"; "o commit foi feito" |
| "Nenhum float no registro" | Detector 1 de `arena-invariantes` vazio **e** nível 5 passando | "pydantic validou"; "o schema aceitou" |
| "O hash é verificável em público" | Nível 5 verde **e** o botão do painel dizendo PASSOU no navegador | "o hash em Python está certo" |
| "Publicou hoje" | Arquivo do dia em `data/` **ou** `OutageRecord` do dia, mais a linha na cadeia | "o cron rodou"; "o workflow ficou verde" |
| "O conector funciona" | Chamada real contra a API, com a saída colada | "os testes com fixture passam" |
| "A parte do Codex está pronta" | Você rodou os seis níveis no branch dele | O relatório dele |
| "Corrigi o bug" | O teste que falhava agora passa, e você viu os dois estados | "mudei a linha que estava errada" |
| "É idempotente" | Rodou o mesmo dia duas vezes e a cadeia continua íntegra | "o código tem `if exists`" |

---

## RED FLAGS

Se você escreveu ou pensou uma destas, pare e rode o nível correspondente:

- "deveria funcionar", "provavelmente", "parece que", "acho que", "deve estar ok"
- "deixa eu só ajustar isso rapidinho" antes de rodar o teste
- "os testes com fixture passam, então a API real funciona"
- "o workflow ficou verde, então publicou"
- **"o outro assistente disse que está pronto"** — relatório de agente não é evidência. Com três assistentes trabalhando em paralelo, este é o red flag mais frequente e o mais caro: o Codex reporta que `ingest/` está pronto, o Antigravity reporta que o painel funciona, e nenhum dos dois rodou o nível 4.
- "vou converter o float na apresentação" — se hasheou float, já corrompeu
- "o schema aceitou" — o schema aceita a string `"0.15"`; o invariante é *nenhum float*, então verifique o tipo

---

## GATE ANTES DE AFIRMAR SUCESSO

1. Rodei o comando? Se não, rode.
2. Li o **exit code**, não só a saída na tela?
3. Contei quantos testes falharam, em vez de olhar o resumo?
4. A afirmação que vou fazer está na tabela "O que prova o quê", e eu tenho o artefato da coluna do meio?
5. Se algo falhou, vou dizer que falhou — com a saída colada — em vez de descrever o que pretendia?

Pular qualquer um destes cinco e afirmar sucesso é mentir, não verificar.

---

## FORMATO DO RELATÓRIO

```
VERIFICAÇÃO — <branch ou PR>

nivel-1-lint          PASSOU   ruff, 0 achados
nivel-2-testes        PASSOU   47 passed
nivel-3-invariantes   PASSOU   8 detectores, saída vazia
nivel-4-cadeia        PASSOU   PASS: 12 entradas, cadeia íntegra
nivel-5-paridade-js   PASSOU   PASS: 6 casos idênticos
nivel-6-ciclo-real    PULADO   sem credencial Alpaca neste ambiente

ZONA RESTRITA TOCADA: não
DIFF EM docs/DECISOES.md: não exigido
```

`PULADO` é uma resposta honesta e aceitável. `PASSOU` sem ter rodado não é.

Quando um nível falha, cole a saída real e pare. Não descreva a falha com suas palavras — a saída é a evidência, sua paráfrase não é.

---

## CHECKLIST DE PR

Cole no corpo do PR. É a interface de handoff assistente → Wilson, que é o único que faz merge.

```
[ ] nivel-1-lint       (exit 0)
[ ] nivel-2-testes     (exit 0, N passed)
[ ] nivel-3-invariantes (8 detectores, saída vazia)
[ ] nivel-4-cadeia     (PASS)
[ ] nivel-5-paridade-js (PASS)
[ ] nivel-6-ciclo-real  (published | already_published | PULADO com motivo)
[ ] Diff abaixo de 400 linhas
[ ] Rebase feito no início da sessão
[ ] Toca zona restrita? (contracts/ canonical.py risk/ metrics/ agents/prompts/ policy/ .github/)
      se sim: PR isolado, nada mais junto, e diff correspondente em docs/DECISOES.md
[ ] Skill seguida: <nome>
```

---

## ARMADILHAS

| Situação | Regra |
|---|---|
| Nível 5 falha só no CI, passa local | Versão de `node` diferente. `arena/canonical.py` é normativo — corrija o JS. |
| Nível 4 falha depois de `git pull` | Alguém reescreveu histórico, ou um registro foi editado. Isso BLOQUEIA e não se conserta com rebase. |
| Nível 6 diz `outage` | Não é falha do gate: é o sistema funcionando. Leia o `reason` no `OutageRecord`. |
| Nível 2 passa mas o ciclo real quebra | Fixture divergiu da API. Regrave a fixture com a saída real. |
| Nível 3 acusa `research/` | Falso positivo: o filtro negativo caiu. Conserte o grep, não o código. |

---

## CONTEXTO

Este projeto vende auditabilidade. Uma afirmação de sucesso não verificada aqui é o mesmo defeito que o projeto se propõe a expor nos agentes de mercado: confiança sem calibração. E a assimetria é grande — o custo de rodar os seis níveis é de minutos, enquanto o custo de um registro corrompido publicado é permanente, porque `data/` e `chain/` são append-only e o erro fica visível para sempre.

## DECISÕES QUE GOVERNAM ESTA SKILL

D2 (8h/semana — por isso os níveis são ordenados por custo), D3 (repositório público), D8 (números como string, que é o que o nível 5 protege). Ver `docs/DECISOES.md`.
