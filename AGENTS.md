# AGENTS.md — briefing operacional

`contracts_version: 1.0.0`

Leia isto no início de toda sessão. Este é o **único** documento de contexto; `CLAUDE.md` e o
arquivo de regras do Antigravity apontam para cá. Três documentos separados reproduziriam o
bug de dialeto um nível acima.

---

## PASSO 0 — REGRA DE PARADA

**Se a decisão que você precisa tomar não está em `docs/DECISOES.md` com Status: Decidida,
PARE e pergunte ao Wilson. Não invente.**

Um assistente que decide formato de divulgação, fonte de verdade da carteira ou nome de
persona às 23h coloca essa escolha no histórico imutável sem que ela tenha sido decidida.

---

## Propriedade por path

| Path | Dono | Zona |
|---|---|---|
| `arena/canonical.py`, `arena/contracts/`, `arena/audit/`, `arena/cycle.py` | Claude Code | restrita |
| `arena/risk/`, `arena/metrics/`, `arena/forecast/`, `policy/`, `.github/` | Claude Code | restrita |
| `arena/ingest/`, `arena/quality/`, `arena/storage/`, `arena/llm/` | Codex | livre |
| `site/`, `apps/` | Antigravity | livre |

Zona restrita muda só por PR **isolado** do Claude Code, aprovado pelo Wilson, com nada mais
no mesmo PR.

---

## Regra de dependência

```
ingest -> storage -> quality -> forecast -> cycle -> audit -> site
```

Nada volta. `arena/canonical.py` não importa nada de `arena/`. `risk/` não importa de
`ingest/`. `apps/content/` não importa nada de `arena/`.

**Fronteira semântica:** o Fiscal **detecta**, o Gestor **decide**, a fórmula **dimensiona**,
o Ledger **contabiliza**, o Auditor **carimba**. `quality/` emite flags e não decide nada.

**Invariante de segurança:** nenhum componente que fala com modelo de linguagem tem credencial
de corretora, escrita no banco operacional ou saída de rede arbitrária. Isso resolve prompt
injection por construção — injeção vira tese ruim, nunca ordem.

---

## Convenções inegociáveis

- **Tudo em UTC**, conversão só na apresentação. `ruff` com a regra `DTZ` reprova
  `datetime.now()` sem timezone.
- **Preço sempre `Adjustment.RAW`** mais tabela separada de ações corporativas. O parâmetro é
  opcional na API, então o erro entra por omissão.
- **Nenhum float em registro hasheado.** Números decimais viajam como string, porque o
  verificador que roda no navegador do visitante precisa recomputar o mesmo hash.
  `arena/canonical.py` levanta `TypeError` se encontrar um.
- **Append-only.** Registro publicado nunca é editado. Correção é registro novo.
- **Rejeição, nunca coerção.** `strict=True` e `extra="forbid"` em todo contrato. Valor
  inválido gera `OutageRecord`, nunca um valor consertado.
- **Anualização 252**, retorno simples salvo declaração explícita. `arena/metrics/` é dono
  único: nenhum outro módulo recalcula métrica.
- **Calendário de pregão** via `exchange_calendars`, nunca contagem de dias corridos.
- **Nenhum valor de segredo em arquivo do repositório.** Ele é público. Só nome de variável
  de ambiente.

Detalhes e os pares errado/certo de cada invariante estão na skill `arena-standards`, que é a
dona única deles.

---

## Skills

| Skill | Quando |
|---|---|
| `arena-standards` | Antes de escrever ou editar qualquer arquivo em `arena/`, `policy/`, `scripts/`, `site/` |
| `arena-invariantes` | Antes de abrir PR; ao revisar PR de outro assistente |
| `arena-verificar` | Antes de afirmar que algo está pronto, e antes de commitar ou mergear |
| `arena-drift` | Ao adicionar ou renomear campo de contrato; quando a paridade Python/JS falhar |
| `arena-publicar` | Ao rodar o ciclo diário ou diagnosticar falha do cron |

Anuncie no início da sessão qual skill está seguindo, e registre isso no corpo do PR.

---

## Protocolo git

Worktree e branch por assistente, com prefixo obrigatório:

```bash
git worktree add ../arena-cc  feat/cc/<assunto>   # Claude Code
git worktree add ../arena-cx  feat/cx/<assunto>   # Codex
git worktree add ../arena-ag  feat/ag/<assunto>   # Antigravity
```

- PRs abaixo de ~400 linhas de diff.
- `git fetch && git rebase origin/main` no **início** de toda sessão. Sessão longa sem rebase
  é a causa raiz da maioria dos conflitos neste arranjo.
- Rebase, nunca merge commit: história linear, porque a história **é** a prova.
- **Ninguém faz push em `main`.** O Wilson faz merge uma vez por dia, em janela fixa, na
  ordem das camadas.
- Mudança de contrato é PR isolado, com bump de `schema_version`, migração das fixtures
  douradas e entrada em `docs/DECISOES.md`. O CI recusa diff em `arena/contracts/`,
  `arena/canonical.py` ou `policy/` sem diff correspondente lá.

---

## Reverter, não adaptar

Código fora do contrato é **revertido**. O contrato não é estendido para acomodar código já
escrito — é assim que três dialetos voltam pela porta dos fundos, com aparência de decisão de
design.

---

## Proibições

- `git push --force` em qualquer branch
- reescrever, reordenar ou remover linha de `chain/CHAIN.jsonl`
- editar arquivo já publicado em `data/`
- `git rebase` sobre commit já carimbado pelo OpenTimestamps
- escrever em `data/` ou `chain/` sem passar por `arena/audit/publish.py`
- usar credencial que não seja de paper trading
