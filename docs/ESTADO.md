# Estado do projeto — handoff

**Atualizado:** 2026-07-30 (segunda revisão)
**Para quem retoma:** leia este arquivo, depois `docs/DECISOES.md`, depois o plano do marco
em que estamos. Os três juntos bastam; não é necessário reler o plano mestre original.

---

## 1. Situação em uma frase

**O M0 ESTÁ COMPLETO. Tasks 1 a 7, 42 testes passando.**

O repositório é público em **https://github.com/wilsonnettoo/ai-market-arena**, com a entrada
gênese carimbada no OpenTimestamps e histórico protegido contra reescrita — verificado por
tentativa real de force-push, recusada mesmo com privilégio de administrador.

A prova de anterioridade **existe**. As regras do experimento estão carimbadas antes de
existir qualquer resultado.

**Próximo marco: M1 (gate de dispersão), Tasks 8 e 9.**

---

## 2. O que existe

### Commits (7, todos em `main` local, sem remoto)

```
a4687d3  docs: manifesto de pre-registro, FILL_SPEC datado, politicas e AGENTS.md
0610f71  feat: verificador independente da cadeia via CLI
2ecd57d  feat: cadeia de hash append-only com verificacao de integridade
e13bfe9  docs: handoff completo de estado para troca de modelo
8b0d944  feat: gate de conformidade de contratos por introspeccao
93b0fba  feat: contratos congelados v1.0.0 com rejeicao estrita
bc1baf2  feat: forma canonica de serializacao e sha256, com float proibido
e066172  chore: bootstrap do toolchain e skills do projeto
```

### Código

| Arquivo | Linhas | O que faz |
|---|---:|---|
| `arena/canonical.py` | 51 | `canonical_bytes`, `sha256_hex`, `assert_no_floats`, `GENESIS_PREV_HASH`. **Normativo** — quando o JS divergir, corrija o JS. |
| `arena/contracts/records.py` | 122 | 7 modelos: `_Record`, `Constituent`, `UniverseSnapshot`, `QualityFlag`, `DataQualityReport`, `OutageRecord`, `ForecastRecord`. `Persona` StrEnum. `SCHEMA_VERSION = "1.0.0"`. |
| `arena/audit/chain.py` | 112 | Cadeia append-only. `file_sha256` é dos bytes em disco; `entry_hash` exclui a própria chave. |
| `scripts/check_contracts.py` | 118 | Gate de conformidade por introspecção. Exit 0/1. |
| `scripts/verify_chain.py` | 47 | Verificador independente. Exit 0/1. Cadeia inexistente não é erro. |

Documentos de pré-registro prontos: `MANIFESTO.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`
(stub), `CODEOWNERS`, `docs/FILL_SPEC.md`, `policy/personas.yaml`,
`policy/forecast_rule.yaml`.

Pacotes vazios prontos: `arena/{storage,ingest,quality,forecast}/`.

### Testes (42, todos passando)

`test_canonical.py` (7), `test_contracts.py` (12), `test_check_contracts.py` (5),
`test_chain.py` (13), `test_verify_script.py` (5).

**Atenção com `test_check_contracts.py`:** três testes **modificam** `arena/contracts/records.py`
e restauram em `finally`. Se uma execução for interrompida (Ctrl-C, crash), rode
`git status arena/` e `git checkout arena/contracts/records.py` antes de continuar.

### Skills (5, em `.claude/skills/`)

`arena-standards` (dona única dos invariantes), `arena-invariantes` (auditoria),
`arena-verificar` (6 níveis de gate), `arena-drift` (divergência contrato/Parquet/JS),
`arena-publicar` (caminho de escrita do ciclo). Todas abaixo de 200 linhas.

### Documentos

- `docs/superpowers/specs/2026-07-29-ai-market-arena-design.md` — spec do ano 1
- `docs/superpowers/plans/2026-07-29-m0-m1-selo-genese-e-gate.md` — M0/M1, Tasks 1–9
- `docs/superpowers/plans/2026-07-29-m2-o-pulso.md` — M2, Tasks 10–19
- `docs/DECISOES.md` — D1 a D19 (11 decididas, 8 pendentes)

---

## 3. M0 — concluído

| Task | Entrega | Commit |
|---|---|---|
| 1 | Bootstrap do toolchain e as 5 skills | `e066172` |
| 2 | Forma canônica e hash, paridade JS provada | `bc1baf2` |
| 3 | Contratos congelados v1.0.0 | `93b0fba` |
| — | Gate de conformidade por introspecção | `8b0d944` |
| 4 | Cadeia de hash append-only | `2ecd57d` |
| 5 | Verificador independente via CLI | `0610f71` |
| 6 | Manifesto, FILL_SPEC, políticas, AGENTS.md | `a4687d3` |
| 7 | **Gênese carimbado e repositório público** | `485b5d1` |

### Estado do gênese

- `entry_hash`: `3e47602d6cc77eff47c379a0fda66dabab392cdd45f38b9fc8cdf976c316ffd8`
- `prev_hash`: 64 zeros
- `created_at_utc`: `2026-07-30T12:06:54Z`
- Cobre: `MANIFESTO.md`, `docs/FILL_SPEC.md`, `policy/personas.yaml`,
  `policy/forecast_rule.yaml`, `AGENTS.md`
- SHA-256 do `chain/CHAIN.jsonl` carimbado:
  `27845ed0a18c50aeac373ecbef43bc3d3ddcdf5121dad7bdafbf9483ff1eae77`
- Atestação submetida a 4 calendários; **pendente de agregação**

### Proteção verificada por teste, não por afirmação

Duas tentativas reais de reescrever história foram recusadas com
`protected branch hook declined`, agindo como administrador:

```bash
git push --force origin HEAD~1:main        # recusado
git push --force origin <historia-alternativa>:main   # recusado
git push origin --delete main              # recusado
```

Configuração confirmada: `enforce_admins: true`, `allow_force_pushes: false`,
`allow_deletions: false`, `required_linear_history: true`.

### Duas pendências operacionais do M0

1. **`ots upgrade` daqui a alguns dias.** A atestação nasce pendente de agregação e só
   confirma o bloco do Bitcoin depois. Rodar e commitar:
   ```bash
   ots upgrade chain/CHAIN.jsonl.ots && git add chain/ && \
     git commit -m "data: upgrade da atestacao OTS" && git push
   ```

2. **Registrar a chave de assinatura no GitHub — exige ação do Wilson.** A CLI não tem o
   escopo necessário. Os commits **já são assinados** (chave em
   `~/.ssh/id_ed25519_arena`, verificação local via `~/.ssh/allowed_signers`), mas o GitHub
   só exibe "Verified" depois de:
   ```bash
   gh auth refresh -h github.com -s admin:ssh_signing_key
   gh api -X POST user/ssh_signing_keys -f title="arena-signing" \
     -f key="$(cat ~/.ssh/id_ed25519_arena.pub)"
   ```
   Considerar também ligar `required_signatures` na proteção da branch depois disso.

## 4. O que falta — M1 (Tasks 8 e 9)

Gate de dispersão. `research/dispersion_gate.py` + relatório em `reports/dispersion-gate.md`.

**Critério escrito antes de rodar:** se mais de 80% da dispersão entre as três carteiras
aleatórias vier do nível de caixa obrigatório, o gate **reprova** e as personas são
redesenhadas (igualar o caixa-alvo e diferenciar por horizonte e pool de candidatos) antes
de qualquer código de produção. Exit 0 = aprovado, exit 2 = reprovado.

Correção já aplicada ao plano por causa do pandas 3.x: usar
`pd.DatetimeIndex(retornos.index).to_period("M")`, nunca `retornos.index.to_period("M")`.

---

## 5. O que falta — M2 (Tasks 10 a 19)

| Task | Módulo | Nota |
|---|---|---|
| 10 | `arena/storage/archive.py` | Arquivo write-once, `gzip` com `mtime=0` para bytes idênticos. `sha256` é do payload **descomprimido**. |
| 11 | `arena/ingest/calendar_us.py` | `exchange_calendars`, `XNYS`. Se o teste do 4 de julho falhar, ajuste **o teste**, não o código: o pacote é a fonte de verdade. |
| 12 | `arena/ingest/alpaca_eod.py` + `arena/storage/bars.py` | `Adjustment.RAW` e `asof` obrigatórios. **Passo pendente de mundo real:** descobrir qual feed a conta acessa (`iex` vs `sip`) e registrar em D16. Gravar fixture `tests/fixtures/bars_sample.json`. |
| 13 | `arena/ingest/universe.py` | CSV de holdings da Invesco. Fonte gratuita **sem contrato** — URL e cabeçalho podem mudar. Verificar ao vivo e registrar em D17. Fixture com espaço à direita nos tickers (o arquivo real vem assim). |
| 14 | `arena/quality/checks.py` | 4 asserções bloqueantes. Retorno extremo isola o papel, **não** derruba o dia. |
| 15 | `arena/forecast/momentum.py` | Regra congelada em `policy/forecast_rule.yaml`. `p_up` idêntico nas 3 personas nesta versão — declarar no manifesto. |
| 16 | `arena/forecast/resolve.py` | **Além do plano original** (a spec põe em M8), ~0,5 dia-pessoa. É a primeira coisa a cortar se a velocidade cair. Empate exato conta como `miss`, por escolha declarada. |
| 17 | `arena/audit/publish.py` + `arena/cycle.py` + `arena/cli.py` | `daily_cycle` recebe IO por `deps` — testável offline e prepara Champion/Challenger. Falha em qualquer estágio publica `OutageRecord`. |
| 18 | `.github/workflows/{ci,daily}.yml` | Cron `0 22 * * 1-5` cobre EDT e EST. Job `contract-guard` reprova diff em contracts/policy sem diff em DECISOES. |
| 19 | `site/*` + `scripts/{build_site,check_js_parity}.py` + `pages.yml` | Testar que o verificador **detecta fraude**, não só que diz PASSOU. |

---

## 6. Armadilhas descobertas na prática — não perder

| # | Armadilha | Regra |
|---|---|---|
| A1 | **zsh expande `--include=*.py`** e o grep falha com `no matches found` | Sempre `--include='*.py'` com quotes. Já corrigido nos 15 usos da skill. |
| A2 | **`strict=True` recusa `str` → `StrEnum`** | `Annotated[Persona, Field(strict=False)]` só no campo `persona`. Ver D19. Sem isso, o registro publicado é ilegível pelo resolvedor e pelo painel. |
| A3 | **`grep -L` não serve para checagem por classe** | Um arquivo com um modelo correto e um errado passa limpo. Use `scripts/check_contracts.py` (introspecção). |
| A4 | **Comparar contagens de grep dá falso positivo** | O docstring do módulo menciona `strict=True` e infla a contagem. Foi a segunda tentativa a falhar. Introspecção é imune. |
| A5 | **pandas 3.0.5: `Index.to_period` falha** | Só existe em `DatetimeIndex`. Use `pd.DatetimeIndex(idx).to_period("M")`. |
| A6 | **pandas 3.0.5: `reindex` de coluna ausente devolve `np.float64(nan)`**, não `None` | O `.map` posterior converte para `None`, então o contrato do store se mantém. Não "conserte". |
| A7 | `pytest` exit **5** significa nenhum teste coletado | Não é falha. |
| A8 | `uv pip download` não existe no uv 0.11.2 | Para testar wheel, rode `uv sync` de verdade. |
| A9 | `.claude/settings.local.json` é ignorado pelo gitignore global | Está em `~/.config/git/ignore`. Não tem segredo. |
| A10 | Testes destrutivos em `test_check_contracts.py` | Restauram em `finally`. Se interrompido, `git checkout arena/contracts/records.py`. |
| A11 | **Ordem visual das decisões** | O arquivo tem D1–D16, depois D19, D18, D17. Cosmético (as inserções foram no topo do bloco). Não reordenar sem necessidade — append-only. |

### Fatos técnicos confirmados

- **Python 3.14.3 funciona.** Não fixar 3.13. Wheels: pydantic 2.13.4, pandas 3.0.5,
  pyarrow 25.0.0, exchange-calendars 4.13.2, ruff 0.16.0, pytest 9.1.1.
- **Paridade Python↔JavaScript está PROVADA** em 8 casos, incluindo `\x01`, `\x1f`, `\x7f`,
  emoji, japonês, acentos, aspas escapadas e barra invertida. A premissa central do projeto
  se sustenta.
- **Golden hash de `{"a":"1"}` = `9afeb0f2b203f254312ec8ded441d0318b7c34c57f8695ede42d2215a30c0960`.**
  Se esse valor mudar, toda a cadeia publicada fica inválida.

---

## 7. Decisões pendentes que bloqueiam trabalho

| ID | Decisão | Bloqueia |
|---|---|---|
| **D10** | Nome do agente agressivo. "Valentão" em pt-BR = quem intimida (*bully*), não quem assume risco. Recomendação: "O Afoito". | `policy/personas.yaml` e identidade visual — **entram na Task 6, agora** |
| D11 | Idioma e público-alvo (decisão jurídica, não editorial) | Linguagem do manifesto e do painel |
| D12 | Wilson narra e assina, ou faceless com TTS. Recomendação: híbrido, agentes nunca em 1ª pessoa aconselhando | Pipeline editorial (M9) |
| D13 | Orçar advogado de mercado de capitais | Nada tecnicamente |
| D14 | Página de posições pessoais do autor | Conteúdo do painel |
| D15 | Uma coluna ou três até o M7 (`p_up` idêntico). Recomendação: uma | Painel (Task 19) |
| D16 | Feed do Alpaca — só a execução revela | Task 12 |
| D17 | Fonte da composição do QQQ — só a execução revela | Task 13 |

O identificador técnico `agressivo` é estável e **não muda** com a decisão editorial de D10.

---

## 8. Comandos

```bash
# gates, na ordem de custo (skill arena-verificar)
uv run ruff check .                              # nivel-1
uv run pytest -q                                 # nivel-2  (24 passando)
uv run python scripts/check_contracts.py         # gate de contratos
uv run python scripts/verify_chain.py            # nivel-4  (ainda não existe — Task 5)
uv run python scripts/check_js_parity.py         # nivel-5  (ainda não existe — Task 19)

# golden hash
uv run python -c "from arena.canonical import sha256_hex; print(sha256_hex({'a':'1'}))"
```

---

## 9. Protocolo dos três assistentes — status

**Ainda não ativado.** A semana zero é serial: só Claude Code até os contratos estarem
mergeados. Os contratos já existem, mas `AGENTS.md`, `CODEOWNERS` e o esqueleto de CI
**não** — eles entram na Task 6. Codex e Antigravity **não devem abrir** antes disso, porque
paralelizar antes dos contratos é matematicamente garantido produzir três dialetos.

Quando ativar: worktree e branch por assistente (`feat/cc/*`, `feat/cx/*`, `feat/ag/*`),
hook de pre-commit lendo `ARENA_AGENT`, um slot de merge por dia feito só pelo Wilson.
Antigravity não começa antes do M2 fechar o loop determinístico.

---

## 10. Restrição operacional atual

**O limite mensal de gasto da conta foi atingido durante esta sessão.** Subagentes e
workflows falham com `You've hit your monthly spend limit`. Duas sínteses de workflow foram
perdidas por isso e refeitas manualmente. Enquanto o limite não subir, trabalhe inline —
não tente despachar agentes.
