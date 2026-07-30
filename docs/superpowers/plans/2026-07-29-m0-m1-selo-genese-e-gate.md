# M0–M1: Selo Gênese e Gate de Dispersão — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Colocar no ar um registro público, hasheado e ancorado externamente, que publica sozinho uma grade diária de previsões probabilísticas determinísticas sobre o Nasdaq-100 — sem uma única chamada de LLM — e validar antes disso se as três personas produzem dispersão real.

**Architecture:** Três marcos sequenciais. M0 congela os contratos, a forma canônica de serialização e a cadeia de hash, e carimba o commit gênese no OpenTimestamps antes de existir qualquer resultado. M1 é pesquisa descartável que decide se "três filosofias" é premissa real ou propaganda. M2 é o ciclo diário: coleta EOD, arquivo write-once, Fiscal de Dados, grade de previsões por momentum transversal, encadeamento no hash e publicação via GitHub Actions em página estática, com verificador que roda no navegador do visitante.

**Tech Stack:** Python 3.13/3.14 (uv), pydantic v2, pandas + pyarrow (Parquet), alpaca-py (EOD, `Adjustment.RAW`), exchange-calendars, requests, pytest, ruff, opentimestamps-client (CLI), GitHub Actions, GitHub Pages, HTML/JS puro sem build.

## Global Constraints

- **Nenhuma chamada de LLM em M0–M2.** Se um passo parecer exigir uma, o passo está errado.
- **Tudo em UTC.** Conversão para outro fuso só na camada de apresentação. Nenhum `datetime.now()` sem timezone.
- **Preço gravado sempre com `Adjustment.RAW`** mais tabela separada de ações corporativas. Nunca só o ajustado.
- **Todo valor numérico dentro de registro hasheado é serializado como string.** Floats não têm forma canônica reprodutível entre Python e JavaScript, e o verificador do navegador precisa recomputar o mesmo hash.
- **Forma canônica única:** `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`. Definida uma vez, em um só lug, e testada contra a implementação JS.
- **Append-only.** Nenhuma edição destrutiva de registro publicado. Correção é registro novo.
- **Validação com rejeição, nunca coerção.** `model_validate` com `strict` onde possível; saída inválida vira `OutageRecord`, não valor consertado.
- **Anualização 252.** Retorno simples salvo declaração explícita em contrário.
- **Sem Postgres, Redis, Airflow, dbt, TimescaleDB, Grafana, FastAPI, VPS.** SQLite/Parquet + cron do GitHub Actions + HTML estático.
- **Repositório público desde o primeiro commit**, com force-push desabilitado inclusive para admin e commits assinados.
- Nomes formais no código e no painel: `guardiao`, `equilibrista`, e o agressivo (nome pendente de decisão — usar `agressivo` como identificador até `docs/DECISOES.md` resolver). "O Cagão" nunca aparece em identificador, título, tag ou descrição.

---

## File Structure

```
aichannel/
  pyproject.toml                    deps + config de ruff/pytest
  .gitignore  .gitattributes
  MANIFESTO.md                      pré-registro: pergunta, métrica, critérios de fracasso
  README.md                         contador de dias + como verificar
  AGENTS.md                         briefing operacional dos três assistentes
  CLAUDE.md                         stub de uma linha -> AGENTS.md
  CODEOWNERS
  docs/
    DECISOES.md                     ADRs append-only
    FILL_SPEC.md                    como ordem vira execução (datado, implementado no M4)
  policy/
    personas.yaml                   limites das três personas
    forecast_rule.yaml              coeficientes da grade, congelados a priori
  arena/
    canonical.py                    forma canônica + sha256           [núcleo]
    contracts/
      __init__.py                   re-export
      records.py                    ForecastRecord, OutageRecord, DataQualityReport, UniverseSnapshot
      chain.py                      ChainEntry
    audit/
      chain.py                      append + verify da cadeia
      publish.py                    escrita atômica dos artefatos do dia
    storage/
      archive.py                    arquivo write-once com ingestion_time
      bars.py                       store Parquet + as_of
    ingest/
      alpaca_eod.py                 barras diárias RAW
      universe.py                   holdings do QQQ (point-in-time)
      calendar_us.py                calendário de pregão
    quality/
      checks.py                     as 4 asserções bloqueantes
    forecast/
      momentum.py                   grade determinística
      resolve.py                    resolvedor de horizonte
    cycle.py                        daily_cycle: função pura
    cli.py                          entrypoints
  research/
    dispersion_gate.py              M1, descartável
  scripts/
    verify_chain.py                 verificador independente (Python)
  site/
    index.html                      painel estático
    verify.js                       verificador no navegador
  .github/workflows/
    ci.yml                          testes + lint + paridade Python/JS
    daily.yml                       cron pós-fechamento
  chain/CHAIN.jsonl                 uma linha por dia
  data/
    raw/                            arquivo write-once
    bars/                           Parquet
    universe/                       snapshot diário
    forecasts/                      registros publicados
```

**Fronteira:** `canonical.py` não importa nada de `arena/`. `contracts/` importa só `canonical`. `quality/` emite relatório e não decide nada. `cycle.py` é função pura de `(data_as_of, política) -> artefatos`; toda escrita acontece em `audit/publish.py`.

---

## M0 — Selo Gênese

### Task 1: Bootstrap do repositório e toolchain

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `.gitattributes`, `arena/__init__.py`, `tests/__init__.py`

**Interfaces:**
- Consumes: nada.
- Produces: ambiente `uv` funcional; comando `uv run pytest` e `uv run ruff check .`

- [ ] **Step 1: Verificar a versão de Python utilizável**

```bash
cd /Users/netto/aichannel
uv python list --only-installed
```

Se `pandas`, `pyarrow` ou `yfinance` não tiverem wheel para 3.14, fixe 3.13 e siga — não perca tempo compilando:

```bash
uv python pin 3.13
```

- [ ] **Step 2: Criar `pyproject.toml`**

```toml
[project]
name = "arena"
version = "0.1.0"
description = "AI Market Arena — registro publico auditavel de previsoes de mercado"
requires-python = ">=3.12,<3.15"
dependencies = [
    "pydantic>=2.9",
    "pandas>=2.2",
    "pyarrow>=17",
    "requests>=2.32",
    "exchange-calendars>=4.5",
    "alpaca-py>=0.33",
    "pyyaml>=6.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "ruff>=0.6",
    "yfinance>=0.2.40",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["arena"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "DTZ"]
```

`DTZ` é deliberado: ele reprova `datetime.now()` sem timezone, que é a classe de bug mais provável num projeto que carimba tempo.

- [ ] **Step 3: Criar `.gitignore` e `.gitattributes`**

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
.ruff_cache/
data/raw/**/*.gz
!data/raw/.gitkeep
```

`.gitattributes` — impede que normalização de fim de linha altere bytes hasheados:
```
* -text
*.py text eol=lf
*.md text eol=lf
*.yaml text eol=lf
*.json text eol=lf
*.jsonl text eol=lf
```

- [ ] **Step 4: Criar pacotes vazios e instalar**

```bash
mkdir -p arena/contracts arena/audit arena/storage arena/ingest arena/quality arena/forecast
mkdir -p tests research scripts site chain data/raw data/bars data/universe data/forecasts
touch arena/__init__.py arena/contracts/__init__.py arena/audit/__init__.py \
      arena/storage/__init__.py arena/ingest/__init__.py arena/quality/__init__.py \
      arena/forecast/__init__.py tests/__init__.py data/raw/.gitkeep
uv sync
uv run python -c "import pydantic, pandas, pyarrow, exchange_calendars, alpaca; print('ok')"
```

Esperado: `ok`. Se `alpaca` falhar no import, o nome do módulo do `alpaca-py` é `alpaca` — confirme que instalou `alpaca-py` e não `alpaca`.

- [ ] **Step 5: Inicializar git e commitar**

```bash
git init
git add -A
git commit -m "chore: bootstrap do toolchain (uv, pytest, ruff)"
```

---

### Task 2: Forma canônica e hash

Este é o núcleo do projeto. Se estiver errado, a prova de anterioridade não vale nada.

**Files:**
- Create: `arena/canonical.py`
- Test: `tests/test_canonical.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `canonical_bytes(obj: Any) -> bytes`
  - `sha256_hex(obj: Any) -> str` — sha256 hex de `canonical_bytes`
  - `assert_no_floats(obj: Any) -> None` — levanta `TypeError` se encontrar `float` em qualquer profundidade
  - `GENESIS_PREV_HASH: str` = 64 zeros

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_canonical.py
import pytest

from arena.canonical import (
    GENESIS_PREV_HASH,
    assert_no_floats,
    canonical_bytes,
    sha256_hex,
)


def test_chaves_ordenadas_e_sem_espacos():
    assert canonical_bytes({"b": "2", "a": "1"}) == b'{"a":"1","b":"2"}'


def test_ordenacao_e_recursiva():
    obj = {"z": {"y": "1", "x": "2"}, "a": ["3", {"d": "4", "c": "5"}]}
    assert canonical_bytes(obj) == b'{"a":["3",{"c":"5","d":"4"}],"z":{"x":"2","y":"1"}}'


def test_acento_fica_literal_nao_escapado():
    assert canonical_bytes({"t": "ação"}) == '{"t":"ação"}'.encode()


def test_float_e_rejeitado_em_qualquer_profundidade():
    with pytest.raises(TypeError, match="float"):
        assert_no_floats({"a": [{"b": 1.5}]})
    with pytest.raises(TypeError, match="float"):
        canonical_bytes({"p": 0.62})


def test_int_e_bool_sao_permitidos():
    assert canonical_bytes({"n": 5, "ok": True}) == b'{"n":5,"ok":true}'


def test_hash_e_estavel_e_conhecido():
    # golden: se este valor mudar, a cadeia inteira ja publicada fica invalida
    assert sha256_hex({"a": "1"}) == (
        "7f0f7bcdb70e6b2e0ecc0cd8dd7bcc5b23dbf1a29b0e5a0e2b1c2eb2b2c9a4bd"
    )


def test_genesis_prev_hash():
    assert GENESIS_PREV_HASH == "0" * 64
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_canonical.py -v`
Esperado: FAIL com `ModuleNotFoundError: No module named 'arena.canonical'`

- [ ] **Step 3: Implementar**

```python
# arena/canonical.py
"""Forma canonica de serializacao e hash.

Contrato congelado. Qualquer mudanca aqui invalida toda a cadeia ja publicada,
portanto exige nova temporada e entrada em docs/DECISOES.md.

Regras:
  - chaves ordenadas, sem espacos, UTF-8 literal (sem escape ASCII);
  - floats sao PROIBIDOS: nao possuem forma canonica reproduzivel entre
    Python e JavaScript, e o verificador do navegador precisa recomputar
    exatamente o mesmo hash. Numeros decimais viajam como string.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

GENESIS_PREV_HASH = "0" * 64


def assert_no_floats(obj: Any, path: str = "$") -> None:
    if isinstance(obj, float):
        raise TypeError(
            f"float proibido em registro hasheado em {path}: "
            "serialize valores decimais como string"
        )
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert_no_floats(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            assert_no_floats(v, f"{path}[{i}]")


def canonical_bytes(obj: Any) -> bytes:
    assert_no_floats(obj)
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()
```

- [ ] **Step 4: Rodar; corrigir o golden**

Run: `uv run pytest tests/test_canonical.py -v`

Todos passam menos `test_hash_e_estavel_e_conhecido` — o valor no teste é um marcador. Obtenha o real e substitua no teste:

```bash
uv run python -c "from arena.canonical import sha256_hex; print(sha256_hex({'a':'1'}))"
```

Cole o valor impresso no teste e rode de novo. Esperado: 7 passed.

Este golden não é cerimônia: ele é o que detecta que alguém mudou a serialização depois de meses de registro publicado.

- [ ] **Step 5: Commitar**

```bash
git add arena/canonical.py tests/test_canonical.py
git commit -m "feat: forma canonica de serializacao e sha256, com float proibido"
```

---

### Task 3: Contratos congelados

**Files:**
- Create: `arena/contracts/records.py`, `arena/contracts/__init__.py`
- Test: `tests/test_contracts.py`

**Interfaces:**
- Consumes: `arena.canonical.sha256_hex`
- Produces:
  - `Persona` — `StrEnum`: `AGRESSIVO`, `EQUILIBRISTA`, `GUARDIAO`
  - `ForecastRecord` — campos: `schema_version: str`, `record_type: Literal["forecast"]`, `emitted_at_utc: str`, `session_date: str`, `resolution_session_date: str`, `horizon_sessions: int`, `persona: Persona`, `symbol: str`, `claim: Literal["outperform_qqq"]`, `p_up: str`, `rule_version: str`, `reference_close_raw: str`, `reference_close_qqq_raw: str`, `universe_snapshot_sha256: str`, `outcome: Literal["pending","hit","miss","void"]`, `resolved_at_utc: str | None`
  - `OutageRecord` — `schema_version`, `record_type: Literal["outage"]`, `detected_at_utc: str`, `session_date: str`, `stage: str`, `reason: str`, `detail: str`
  - `DataQualityReport` — `schema_version`, `record_type: Literal["dq"]`, `session_date: str`, `passed: bool`, `flags: list[QualityFlag]`, `quarantined_symbols: list[str]`
  - `QualityFlag` — `code: str`, `severity: Literal["block","warn"]`, `symbol: str | None`, `detail: str`
  - `UniverseSnapshot` — `schema_version`, `record_type: Literal["universe"]`, `session_date: str`, `source: str`, `constituents: list[Constituent]`
  - `Constituent` — `symbol: str`, `weight_pct: str`
  - Todos: `.canonical_dict() -> dict` (`model_dump(mode="json")`) e `.sha256() -> str`
  - `SCHEMA_VERSION: str = "1.0.0"`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_contracts.py
import pytest
from pydantic import ValidationError

from arena.contracts import (
    SCHEMA_VERSION,
    ForecastRecord,
    OutageRecord,
    Persona,
)


def _fc(**over):
    base = dict(
        schema_version=SCHEMA_VERSION,
        record_type="forecast",
        emitted_at_utc="2026-08-03T20:15:00Z",
        session_date="2026-08-03",
        resolution_session_date="2026-08-10",
        horizon_sessions=5,
        persona=Persona.AGRESSIVO,
        symbol="NVDA",
        claim="outperform_qqq",
        p_up="0.5600",
        rule_version="momentum-1.0.0",
        reference_close_raw="174.20",
        reference_close_qqq_raw="480.11",
        universe_snapshot_sha256="a" * 64,
        outcome="pending",
        resolved_at_utc=None,
    )
    base.update(over)
    return base


def test_forecast_valido_e_hasheavel():
    r = ForecastRecord.model_validate(_fc())
    assert len(r.sha256()) == 64
    assert r.canonical_dict()["p_up"] == "0.5600"


def test_p_up_float_e_rejeitado():
    with pytest.raises(ValidationError):
        ForecastRecord.model_validate(_fc(p_up=0.56))


def test_campo_desconhecido_e_rejeitado_nao_ignorado():
    with pytest.raises(ValidationError):
        ForecastRecord.model_validate(_fc(inventado="x"))


def test_timestamp_precisa_terminar_em_Z():
    with pytest.raises(ValidationError):
        ForecastRecord.model_validate(_fc(emitted_at_utc="2026-08-03T20:15:00-03:00"))


def test_p_up_fora_de_zero_um_e_rejeitado():
    with pytest.raises(ValidationError):
        ForecastRecord.model_validate(_fc(p_up="1.5000"))


def test_hash_muda_quando_qualquer_campo_muda():
    a = ForecastRecord.model_validate(_fc()).sha256()
    b = ForecastRecord.model_validate(_fc(symbol="AAPL")).sha256()
    assert a != b


def test_outage_record():
    o = OutageRecord.model_validate(
        dict(
            schema_version=SCHEMA_VERSION,
            record_type="outage",
            detected_at_utc="2026-08-03T20:15:00Z",
            session_date="2026-08-03",
            stage="ingest",
            reason="DATA_UNAVAILABLE",
            detail="HTTP 503 do provedor de barras",
        )
    )
    assert len(o.sha256()) == 64
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_contracts.py -v`
Esperado: FAIL com `ImportError` / `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

```python
# arena/contracts/records.py
"""Contratos congelados. Mudanca exige bump de SCHEMA_VERSION,
migracao das fixtures douradas e entrada em docs/DECISOES.md.
"""

from __future__ import annotations

import re
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from arena.canonical import sha256_hex

SCHEMA_VERSION = "1.0.0"

_UTC_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

DecimalStr = Annotated[str, Field(pattern=r"^-?\d+\.\d+$")]
UtcStamp = Annotated[str, Field(pattern=_UTC_Z.pattern)]
SessionDate = Annotated[str, Field(pattern=_DATE.pattern)]
Sha256Hex = Annotated[str, Field(pattern=_SHA256.pattern)]


class Persona(StrEnum):
    AGRESSIVO = "agressivo"
    EQUILIBRISTA = "equilibrista"
    GUARDIAO = "guardiao"


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    def canonical_dict(self) -> dict:
        return self.model_dump(mode="json")

    def sha256(self) -> str:
        return sha256_hex(self.canonical_dict())


class Constituent(_Record):
    symbol: str = Field(min_length=1, max_length=12)
    weight_pct: DecimalStr


class UniverseSnapshot(_Record):
    schema_version: str
    record_type: Literal["universe"]
    session_date: SessionDate
    source: str
    constituents: list[Constituent]


class QualityFlag(_Record):
    code: str
    severity: Literal["block", "warn"]
    symbol: str | None
    detail: str


class DataQualityReport(_Record):
    schema_version: str
    record_type: Literal["dq"]
    session_date: SessionDate
    passed: bool
    flags: list[QualityFlag]
    quarantined_symbols: list[str]


class OutageRecord(_Record):
    schema_version: str
    record_type: Literal["outage"]
    detected_at_utc: UtcStamp
    session_date: SessionDate
    stage: str
    reason: str
    detail: str


class ForecastRecord(_Record):
    schema_version: str
    record_type: Literal["forecast"]
    emitted_at_utc: UtcStamp
    session_date: SessionDate
    resolution_session_date: SessionDate
    horizon_sessions: int = Field(ge=1, le=252)
    persona: Persona
    symbol: str = Field(min_length=1, max_length=12)
    claim: Literal["outperform_qqq"]
    p_up: DecimalStr
    rule_version: str
    reference_close_raw: DecimalStr
    reference_close_qqq_raw: DecimalStr
    universe_snapshot_sha256: Sha256Hex
    outcome: Literal["pending", "hit", "miss", "void"]
    resolved_at_utc: UtcStamp | None

    @field_validator("p_up")
    @classmethod
    def _p_up_em_zero_um(cls, v: str) -> str:
        if not (Decimal("0") <= Decimal(v) <= Decimal("1")):
            raise ValueError("p_up precisa estar em [0, 1]")
        return v
```

```python
# arena/contracts/__init__.py
from arena.contracts.records import (
    SCHEMA_VERSION,
    Constituent,
    DataQualityReport,
    ForecastRecord,
    OutageRecord,
    Persona,
    QualityFlag,
    UniverseSnapshot,
)

__all__ = [
    "SCHEMA_VERSION",
    "Constituent",
    "DataQualityReport",
    "ForecastRecord",
    "OutageRecord",
    "Persona",
    "QualityFlag",
    "UniverseSnapshot",
]
```

- [ ] **Step 4: Rodar até passar**

Run: `uv run pytest tests/test_contracts.py -v`
Esperado: 7 passed.

Se `test_p_up_float_e_rejeitado` falhar, confirme que `strict=True` está no `ConfigDict` — sem ele pydantic coage `0.56` para `"0.56"` silenciosamente, que é exatamente o modo de falha que este projeto não pode ter.

- [ ] **Step 5: Commitar**

```bash
git add arena/contracts tests/test_contracts.py
git commit -m "feat: contratos congelados v1.0.0 com rejeicao estrita"
```

---

### Task 4: Cadeia de hash

**Files:**
- Create: `arena/audit/chain.py`
- Test: `tests/test_chain.py`

**Interfaces:**
- Consumes: `arena.canonical.{canonical_bytes, sha256_hex, GENESIS_PREV_HASH}`
- Produces:
  - `file_sha256(path: Path) -> str` — hash dos **bytes em disco** (não da forma canônica)
  - `build_entry(session_date: str, created_at_utc: str, paths: list[Path], prev_hash: str, root: Path) -> dict` — devolve dict com `session_date`, `created_at_utc`, `files` (lista de `{path, sha256}` ordenada por path), `prev_hash`, `entry_hash`
  - `append_entry(chain_path: Path, entry: dict) -> None` — grava uma linha JSON canônica
  - `read_chain(chain_path: Path) -> list[dict]`
  - `last_hash(chain_path: Path) -> str` — `GENESIS_PREV_HASH` se vazia
  - `verify_chain(chain_path: Path, root: Path) -> list[str]` — lista de erros; vazia significa íntegra

`entry_hash` = `sha256_hex` do dict sem a chave `entry_hash`.

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_chain.py
from pathlib import Path

from arena.audit.chain import (
    append_entry,
    build_entry,
    last_hash,
    verify_chain,
)
from arena.canonical import GENESIS_PREV_HASH


def _dia(tmp: Path, chain: Path, dia: str, conteudo: str) -> Path:
    f = tmp / f"data/forecasts/{dia}.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(conteudo, encoding="utf-8")
    e = build_entry(dia, f"{dia}T20:15:00Z", [f], last_hash(chain), tmp)
    append_entry(chain, e)
    return f


def test_cadeia_vazia_devolve_genesis(tmp_path):
    assert last_hash(tmp_path / "CHAIN.jsonl") == GENESIS_PREV_HASH


def test_dois_dias_encadeiam_e_verificam(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    _dia(tmp_path, chain, "2026-08-04", '{"a":"2"}')
    assert verify_chain(chain, tmp_path) == []


def test_editar_arquivo_antigo_quebra_a_cadeia(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    f = _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    _dia(tmp_path, chain, "2026-08-04", '{"a":"2"}')
    f.write_text('{"a":"999"}', encoding="utf-8")  # a fraude
    erros = verify_chain(chain, tmp_path)
    assert any("sha256 divergente" in e for e in erros)


def test_remover_arquivo_quebra_a_cadeia(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    f = _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    f.unlink()
    assert any("ausente" in e for e in verify_chain(chain, tmp_path))


def test_reescrever_linha_da_cadeia_quebra_o_elo(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    _dia(tmp_path, chain, "2026-08-04", '{"a":"2"}')
    linhas = chain.read_text(encoding="utf-8").splitlines()
    linhas[0] = linhas[0].replace('"2026-08-03"', '"2026-08-02"')
    chain.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    erros = verify_chain(chain, tmp_path)
    assert any("entry_hash" in e or "prev_hash" in e for e in erros)


def test_primeira_entrada_precisa_apontar_para_genesis(tmp_path):
    chain = tmp_path / "CHAIN.jsonl"
    _dia(tmp_path, chain, "2026-08-03", '{"a":"1"}')
    assert verify_chain(chain, tmp_path) == []
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_chain.py -v`
Esperado: FAIL com `ModuleNotFoundError: No module named 'arena.audit.chain'`

- [ ] **Step 3: Implementar**

```python
# arena/audit/chain.py
"""Cadeia de hash append-only.

Cada entrada carrega o hash da anterior. Editar, remover ou reordenar
qualquer arquivo ja registrado quebra a verificacao — que e exatamente
a propriedade que "PostgreSQL imutavel" e "commit no GitHub" nao dao.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arena.canonical import GENESIS_PREV_HASH, canonical_bytes, sha256_hex


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for bloco in iter(lambda: fh.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def build_entry(
    session_date: str,
    created_at_utc: str,
    paths: list[Path],
    prev_hash: str,
    root: Path,
) -> dict:
    arquivos = sorted(
        ({"path": str(p.relative_to(root).as_posix()), "sha256": file_sha256(p)} for p in paths),
        key=lambda d: d["path"],
    )
    entrada = {
        "session_date": session_date,
        "created_at_utc": created_at_utc,
        "files": arquivos,
        "prev_hash": prev_hash,
    }
    entrada["entry_hash"] = sha256_hex(entrada)
    return entrada


def append_entry(chain_path: Path, entry: dict) -> None:
    chain_path.parent.mkdir(parents=True, exist_ok=True)
    with chain_path.open("ab") as fh:
        fh.write(canonical_bytes(entry) + b"\n")


def read_chain(chain_path: Path) -> list[dict]:
    if not chain_path.exists():
        return []
    return [
        json.loads(linha)
        for linha in chain_path.read_text(encoding="utf-8").splitlines()
        if linha.strip()
    ]


def last_hash(chain_path: Path) -> str:
    entradas = read_chain(chain_path)
    return entradas[-1]["entry_hash"] if entradas else GENESIS_PREV_HASH


def verify_chain(chain_path: Path, root: Path) -> list[str]:
    erros: list[str] = []
    esperado_prev = GENESIS_PREV_HASH

    for i, entrada in enumerate(read_chain(chain_path)):
        rotulo = f"linha {i + 1} ({entrada.get('session_date', '?')})"

        corpo = {k: v for k, v in entrada.items() if k != "entry_hash"}
        recalculado = sha256_hex(corpo)
        if recalculado != entrada.get("entry_hash"):
            erros.append(f"{rotulo}: entry_hash divergente")

        if entrada.get("prev_hash") != esperado_prev:
            erros.append(f"{rotulo}: prev_hash nao aponta para a entrada anterior")

        for arq in entrada.get("files", []):
            destino = root / arq["path"]
            if not destino.exists():
                erros.append(f"{rotulo}: arquivo ausente {arq['path']}")
            elif file_sha256(destino) != arq["sha256"]:
                erros.append(f"{rotulo}: sha256 divergente em {arq['path']}")

        esperado_prev = entrada.get("entry_hash", "")

    return erros
```

- [ ] **Step 4: Rodar até passar**

Run: `uv run pytest tests/test_chain.py -v`
Esperado: 6 passed.

O teste `test_editar_arquivo_antigo_quebra_a_cadeia` é o mais importante do repositório inteiro. Se ele passar por acidente (por exemplo porque `verify_chain` sempre devolve erro), quebre-o de propósito para confirmar: comente a reescrita do arquivo e confirme que a lista volta vazia.

- [ ] **Step 5: Commitar**

```bash
git add arena/audit/chain.py tests/test_chain.py
git commit -m "feat: cadeia de hash append-only com verificacao de integridade"
```

---

### Task 5: Verificador independente em Python

**Files:**
- Create: `scripts/verify_chain.py`
- Test: `tests/test_verify_script.py`

**Interfaces:**
- Consumes: `arena.audit.chain.verify_chain`
- Produces: CLI `uv run python scripts/verify_chain.py [--root .] [--chain chain/CHAIN.jsonl]`; sai com código 0 e imprime `PASS: N entradas` quando íntegra, código 1 e lista de erros quando não.

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_verify_script.py
import subprocess
import sys
from pathlib import Path

from arena.audit.chain import append_entry, build_entry, last_hash

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_chain.py"


def _monta(tmp: Path) -> Path:
    chain = tmp / "chain" / "CHAIN.jsonl"
    f = tmp / "data" / "x.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text('{"a":"1"}', encoding="utf-8")
    append_entry(chain, build_entry("2026-08-03", "2026-08-03T20:15:00Z", [f], last_hash(chain), tmp))
    return chain


def _roda(tmp: Path, chain: Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp), "--chain", str(chain)],
        capture_output=True,
        text=True,
    )


def test_cadeia_intacta_sai_zero(tmp_path):
    r = _roda(tmp_path, _monta(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS" in r.stdout


def test_cadeia_corrompida_sai_um(tmp_path):
    chain = _monta(tmp_path)
    (tmp_path / "data" / "x.json").write_text('{"a":"2"}', encoding="utf-8")
    r = _roda(tmp_path, chain)
    assert r.returncode == 1
    assert "sha256 divergente" in r.stdout
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_verify_script.py -v`
Esperado: FAIL — o script não existe.

- [ ] **Step 3: Implementar**

```python
# scripts/verify_chain.py
"""Verificador independente da cadeia de hash.

Uso:
    uv run python scripts/verify_chain.py
    uv run python scripts/verify_chain.py --root . --chain chain/CHAIN.jsonl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arena.audit.chain import read_chain, verify_chain  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--chain", default="chain/CHAIN.jsonl")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    chain = Path(args.chain)
    if not chain.is_absolute():
        chain = root / chain

    erros = verify_chain(chain, root)
    if erros:
        print(f"FAIL: {len(erros)} problema(s)")
        for e in erros:
            print(f"  - {e}")
        return 1

    print(f"PASS: {len(read_chain(chain))} entradas, cadeia integra")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Rodar até passar**

Run: `uv run pytest tests/test_verify_script.py -v`
Esperado: 2 passed.

- [ ] **Step 5: Commitar**

```bash
git add scripts/verify_chain.py tests/test_verify_script.py
git commit -m "feat: verificador independente da cadeia via CLI"
```

---

### Task 6: Documentos do pré-registro e política

Nenhum código. É o conteúdo cujo valor é ser **datado antes** de existir resultado.

**Files:**
- Create: `MANIFESTO.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `CODEOWNERS`, `docs/FILL_SPEC.md`, `policy/personas.yaml`, `policy/forecast_rule.yaml`
- **Já existe, não recriar:** `docs/DECISOES.md` — escrito em 2026-07-29 com D1 a D17 (nove decididas, oito pendentes). Sobrescrevê-lo apagaria decisões já tomadas, o que é exatamente o que o arquivo existe para impedir.

**Interfaces:**
- Consumes: nada.
- Produces: `policy/forecast_rule.yaml` com `version`, `weights.rel_20`, `weights.rel_60`, `p_min`, `p_max`, `horizon_sessions`, `universe_top_n` — lidos pela Task 14. `policy/personas.yaml` lido pela Task 8.

- [ ] **Step 1: `MANIFESTO.md`**

```markdown
# Manifesto — AI Market Arena

Documento de pré-registro. Escrito e carimbado antes de existir a primeira previsão.
Correções são feitas por acréscimo, nunca por edição.

## A pergunta

Três políticas de decisão com filosofias de risco declaradamente diferentes, operando
capital fictício sobre o mesmo universo (Nasdaq-100), produzem previsões
mensuravelmente melhores que o azar e que baselines triviais?

## A métrica-manchete

Brier Skill Score contra climatologia, com intervalo de confiança por bootstrap.
Baselines obrigatórios publicados ao lado, sempre: climatologia, moeda justa (0,50),
otimista fixo (0,55) e momentum 12-1.

## Como o fracasso é declarado

O desfecho mais provável é habilidade não mensurável — Brier Skill Score próximo de
zero com intervalo de confiança cruzando zero. **Esse resultado será publicado com o
mesmo destaque de um resultado positivo.** Nenhuma regra, prompt, limite ou
coeficiente é alterado para melhorar um número já publicado.

## O que este projeto não afirma

Que a IA prevê o futuro. Que existe taxa de acerto garantida. Que o sistema supera o
Nasdaq. Que alguém deve copiar qualquer operação. Que resultado passado se repete.
Que paper trading representa o mercado real.

## Regras de integridade

1. Todo registro é publicado antes do resultado.
2. `entry_limit`, `stop` e `target` são publicados sob hash em T0 e revelados no
   fechamento do horizonte. Todo o resto vai em claro em T0.
3. Nenhum registro publicado é editado. Correção é registro novo.
4. Cada dia de pregão gera registro. Dia sem publicação gera `OutageRecord` —
   silêncio nunca.
5. A regra de previsão e seus coeficientes são congelados antes da primeira
   previsão e versionados em `policy/forecast_rule.yaml`.
6. Nenhuma chamada de LLM participa das previsões publicadas antes do marco M7,
   e a data da transição é anunciada e carimbada antes de acontecer.

## Como auditar

    uv run python scripts/verify_chain.py

O verificador recomputa a cadeia inteira a partir do gênese e confere o hash de cada
arquivo em disco. `chain/CHAIN.jsonl.ots` é a atestação OpenTimestamps, ancorada no
Bitcoin: ela prova que o conteúdo existia antes do bloco que a contém.

## Capital

Fictício. Sempre. Nenhuma credencial de conta real está acessível ao sistema.
```

- [ ] **Step 2: `policy/forecast_rule.yaml`**

Coeficientes escolhidos **a priori**, não ajustados a dado nenhum. Faixa deliberadamente estreita porque a regra é conhecidamente ingênua.

```yaml
version: momentum-1.0.0
frozen_at_utc: "2026-08-03T00:00:00Z"
claim: outperform_qqq
horizon_sessions: 5
universe_top_n: 25
lookbacks:
  rel_20: 20
  rel_60: 60
weights:
  rel_20: "0.60"
  rel_60: "0.40"
mapping:
  method: cross_sectional_percentile
  p_min: "0.42"
  p_max: "0.58"
notes: >
  p_up = p_min + (p_max - p_min) * percentil_transversal(score), onde
  score = 0.60 * forca_relativa_20d + 0.40 * forca_relativa_60d contra QQQ.
  Coeficientes definidos a priori, sem ajuste a dados historicos. A regra e
  intencionalmente ingenua: seu papel e comecar a acumular amostra e servir de
  grupo de controle permanente para os agentes de LLM que entram no M7.
```

- [ ] **Step 3: `policy/personas.yaml`**

```yaml
version: personas-1.0.0
frozen_at_utc: "2026-08-03T00:00:00Z"
personas:
  agressivo:
    nome_formal: "(pendente — ver docs/DECISOES.md #1)"
    horizonte_pregoes: [1, 10]
    risco_max_por_operacao_pct: "1.00"
    posicao_max_pct: "8.00"
    posicoes_simultaneas_max: 5
    perda_max_diaria_pct: "2.00"
    caixa_min_pct: "0.00"
    etfs_permitidos: false
  equilibrista:
    nome_formal: "O Equilibrista"
    horizonte_pregoes: [10, 126]
    risco_max_por_operacao_pct: "0.75"
    posicao_max_pct: "8.00"
    posicoes_simultaneas_max: 10
    perda_max_diaria_pct: "2.00"
    caixa_min_pct: "15.00"
    etfs_permitidos: false
  guardiao:
    nome_formal: "O Guardião"
    horizonte_pregoes: [126, 1260]
    risco_max_por_operacao_pct: "0.50"
    posicao_max_pct: "5.00"
    posicoes_simultaneas_max: 20
    perda_max_diaria_pct: "2.00"
    caixa_min_pct: "0.00"
    etfs_permitidos: true
```

- [ ] **Step 4: `docs/FILL_SPEC.md`**

Escrito agora, implementado no M4. O valor está em ser datado antes do simulador existir — preenchimento é função pura de (ordem, barras posteriores), e as barras ficam arquivadas.

```markdown
# FILL_SPEC v1.0.0

Datado em 2026-08-03. Implementado no marco M4. Congelado: mudança exige bump de
versão, entrada em `docs/DECISOES.md` e nova temporada.

Preenchimento é função pura de `(ordem, barras posteriores)`. Como toda barra é
arquivada com `ingestion_time`, a carteira pode ser reconstruída por qualquer
terceiro a partir deste documento — e por isso o Ledger não custa calendário.

## Ciclo de vida da ordem

`proposta -> publicada -> ativa -> {parcial -> preenchida | preenchida | stopada | expirada} -> encerrada`

Ordem que nunca preenche termina em `expirada` e **permanece no histórico**. A taxa
de não-preenchimento é métrica de capa. Ordem que evapora do registro é o mecanismo
número um de inflação de track record.

## Regras

1. **LIMIT de compra.** Preenche no pregão seguinte à publicação se
   `low <= entry_limit`. Preço de execução = `min(open, entry_limit)`. Validade: 2
   pregões; depois, `expirada`.
2. **Gap.** Se `open <= entry_limit`, executa em `open`, nunca em `entry_limit`.
3. **STOP.** Ordem repousando, avaliada contra o OHLC de cada pregão. Se
   `low <= stop`, executa em `min(open, stop)`. Em gap de abertura abaixo do stop,
   executa em `open`.
4. **TARGET.** Se `high >= target`, executa em `max(open, target)`.
5. **Stop e target no mesmo pregão.** Assume-se o pior caso: stop primeiro.
   Barra diária não permite ordenar os dois eventos, e supor o melhor caso é a
   forma mais comum de inflar backtest.
6. **Parcial.** Se o tamanho da ordem exceder 1% do volume do pregão, preenche
   apenas 1% do volume; o restante segue ativo até expirar.
7. **Custos.** Comissão zero (corretora americana de varejo). Slippage de 1 ponto-base
   aplicado contra a posição em toda execução. Spread já embutido na regra de gap.
8. **Ações corporativas.** Split ajusta quantidade e todos os preços da ordem pelo
   fator, na data efetiva. Dividendo credita caixa. Nenhum preço ajustado é gravado:
   o cálculo parte sempre do bruto mais a tabela de ações corporativas.
9. **Deslistagem ou saída do índice.** Posição encerrada no último fechamento
   disponível; ordens ativas viram `expirada`. A previsão associada vira `void`.
```

- [ ] **Step 5: `AGENTS.md`, `CLAUDE.md`, `CODEOWNERS`, `docs/DECISOES.md`, `README.md`**

`AGENTS.md`:
```markdown
# AGENTS.md — briefing operacional

`contracts_version: 1.0.0`

Leia isto no início de toda sessão. Este é o único documento de contexto;
`CLAUDE.md` e o arquivo de regras do Antigravity apontam para cá.

## Propriedade por path

| Path | Dono | Zona restrita |
|---|---|---|
| `arena/canonical.py`, `arena/contracts/`, `arena/audit/`, `arena/cycle.py` | Claude Code | sim |
| `arena/forecast/`, `policy/` | Claude Code | sim |
| `arena/ingest/`, `arena/quality/`, `arena/storage/` | Codex | não |
| `site/`, `apps/` | Antigravity (a partir do M2) | não |
| `.github/`, `pyproject.toml` | Claude Code | sim |

Zona restrita muda só por PR isolado do Claude Code, aprovado pelo Wilson.

## Regra de dependência

`ingest -> storage -> quality -> forecast -> cycle -> audit -> site`. Nada volta.
`arena/canonical.py` não importa nada de `arena/`.

## Fronteira semântica

O Fiscal **detecta**, o Gestor **decide**, a fórmula **dimensiona**, o Auditor
**carimba**. `quality/` emite flags e não decide nada.

## Convenções inegociáveis

- Tudo em UTC; conversão só na apresentação. `ruff` reprova `datetime.now()` sem tz.
- Preço sempre `Adjustment.RAW` mais tabela separada de ações corporativas.
- Todo número dentro de registro hasheado é string. Floats são proibidos por código.
- Anualização 252. Retorno simples salvo declaração explícita.
- Calendário de pregão via `exchange_calendars`, nunca contagem de dias.
- Validação com rejeição, nunca coerção.

## Regra de parada

**Se a decisão que você precisa tomar não está em `docs/DECISOES.md`, PARE e
pergunte ao Wilson. Não invente.**

## Reverter, não adaptar

Código fora do contrato é revertido. O contrato não é estendido para acomodar
código já escrito — é assim que três dialetos voltam com aparência de design.

## Protocolo git

Worktree e branch por assistente (`feat/cc/*`, `feat/cx/*`, `feat/ag/*`). PRs abaixo
de 400 linhas. Rebase no início de toda sessão. Ninguém faz push em `main`; o Wilson
faz merge uma vez por dia, na ordem das camadas.
```

`CLAUDE.md`:
```markdown
Veja [AGENTS.md](./AGENTS.md). Este arquivo é intencionalmente um stub: três
documentos de contexto separados reproduziriam o bug de dialeto um nível acima.
```

`CODEOWNERS`:
```
/arena/canonical.py   @netto
/arena/contracts/     @netto
/arena/audit/         @netto
/arena/cycle.py       @netto
/arena/forecast/      @netto
/policy/              @netto
/.github/             @netto
/pyproject.toml       @netto
/MANIFESTO.md         @netto
/docs/FILL_SPEC.md    @netto
```

`docs/DECISOES.md` — **já existe, NÃO recriar.** Foi escrito em 2026-07-29 com
D1 a D17: nove decisões já tomadas (produto é o registro, capacidade e orçamento,
repositório público desde o dia 1, formato T0, sem VPS, backtest no motor de produção,
preço bruto, números como string, Liga Crypto removida) e oito pendentes (nome do agente
agressivo, idioma e público-alvo, autoria editorial, advogado, posições pessoais do autor,
exibição do `p_up` até o M7, feed do Alpaca, fonte da composição do QQQ).

Sobrescrever esse arquivo apagaria decisões já tomadas — que é exatamente o que ele existe
para impedir. Confira que ele está no lugar e siga:

```bash
test -f docs/DECISOES.md && grep -c '^### D' docs/DECISOES.md
```

Esperado: `17`. As entradas D16 e D17 são preenchidas durante a execução do M2, nas Tasks
12 e 13.

`README.md`:
```markdown
# AI Market Arena

Registro público e auditável de previsões de mercado, publicadas antes do resultado.
Capital fictício. Experimento educacional, **não** recomendação de investimento.

**Temporada Zero — sistema em validação.**

Leia o [Manifesto](./MANIFESTO.md): a pergunta, a métrica e como o fracasso será
declarado, escritos antes da primeira previsão existir.

## Verifique você mesmo

    uv run python scripts/verify_chain.py

Recomputa a cadeia de hash a partir do gênese e confere o hash de cada arquivo em
disco. `chain/CHAIN.jsonl.ots` prova, via OpenTimestamps e Bitcoin, que o conteúdo
existia antes do bloco que o ancora.
```

- [ ] **Step 6: Validar que os YAML carregam e commitar**

```bash
uv run python -c "
import yaml
for f in ('policy/personas.yaml','policy/forecast_rule.yaml'):
    d = yaml.safe_load(open(f))
    print(f, d['version'])
"
uv run ruff check .
git add -A
git commit -m "docs: manifesto de pre-registro, FILL_SPEC datado, politicas e AGENTS.md"
```

Esperado: as duas versões impressas e `ruff` sem erro.

---

### Task 7: Commit gênese, carimbo externo e proteção do histórico

Aqui a promessa central deixa de ser prosa.

**Files:**
- Create: `chain/CHAIN.jsonl`, `chain/CHAIN.jsonl.ots`

**Interfaces:**
- Consumes: `arena.audit.chain.{build_entry, append_entry, last_hash}`
- Produces: primeira entrada da cadeia, apontando para `GENESIS_PREV_HASH`, cobrindo os arquivos de pré-registro; atestação OpenTimestamps commitada ao lado.

- [ ] **Step 1: Instalar o cliente OpenTimestamps e conferir**

```bash
uv tool install opentimestamps-client
ots --version
```

Se `uv tool install` falhar, use `pipx install opentimestamps-client`. Se as duas falharem, **pare e registre o bloqueio** — o carimbo externo não é opcional: sem ele, a data de anterioridade é apenas a sua palavra.

- [ ] **Step 2: Criar a entrada gênese**

```bash
uv run python - <<'PY'
from datetime import datetime, timezone
from pathlib import Path

from arena.audit.chain import append_entry, build_entry, last_hash

root = Path(".").resolve()
chain = root / "chain" / "CHAIN.jsonl"
alvos = [
    root / "MANIFESTO.md",
    root / "docs" / "FILL_SPEC.md",
    root / "policy" / "personas.yaml",
    root / "policy" / "forecast_rule.yaml",
    root / "AGENTS.md",
]
faltando = [str(p) for p in alvos if not p.exists()]
assert not faltando, f"arquivos ausentes: {faltando}"

agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
entrada = build_entry("genesis", agora, alvos, last_hash(chain), root)
append_entry(chain, entrada)
print("entry_hash:", entrada["entry_hash"])
print("prev_hash :", entrada["prev_hash"])
PY
```

Esperado: `prev_hash` com 64 zeros.

- [ ] **Step 3: Verificar antes de carimbar**

```bash
uv run python scripts/verify_chain.py
```

Esperado: `PASS: 1 entradas, cadeia integra`. **Não prossiga se falhar** — carimbar uma cadeia quebrada carimba o defeito.

- [ ] **Step 4: Carimbar e commitar**

```bash
ots stamp chain/CHAIN.jsonl
ls -la chain/CHAIN.jsonl.ots
git add chain/ && git commit -m "feat: entrada genesis da cadeia, carimbada no OpenTimestamps"
```

A atestação nasce incompleta (pendente de agregação). Rode `ots upgrade chain/CHAIN.jsonl.ots` alguns dias depois e commite o resultado; `ots verify` só confirma o bloco após a agregação.

- [ ] **Step 5: Publicar o repositório e travar o histórico**

```bash
gh repo create ai-market-arena --public --source=. --remote=origin --push
gh api -X PUT repos/:owner/ai-market-arena/branches/main/protection \
  --input - <<'JSON'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_linear_history": true
}
JSON
```

`enforce_admins: true` é o ponto: sem ele você continua podendo reescrever o histórico, e a prova de anterioridade vale zero. Confirme:

```bash
gh api repos/:owner/ai-market-arena/branches/main/protection \
  --jq '{force: .allow_force_pushes.enabled, admins: .enforce_admins.enabled, linear: .required_linear_history.enabled}'
```

Esperado: `{"force": false, "admins": true, "linear": true}`.

- [ ] **Step 6: Ligar assinatura de commits**

```bash
git config --local commit.gpgsign true
git config --local gpg.format ssh
git config --local user.signingkey ~/.ssh/id_ed25519.pub
gh api -X POST user/ssh_signing_keys -f title="arena" -f key="$(cat ~/.ssh/id_ed25519.pub)"
git commit --allow-empty -S -m "chore: habilita assinatura de commits"
git log --show-signature -1 | head -5
git push
```

Se não houver `~/.ssh/id_ed25519.pub`, crie com `ssh-keygen -t ed25519 -C arena`.

**M0 concluído.** Existe um repositório público com regras carimbadas no Bitcoin antes de qualquer resultado, histórico não reescrevível, e um verificador que qualquer estranho roda.

---

## M1 — Gate de Dispersão

Pesquisa descartável que decide se "três filosofias" é premissa real. Nada daqui vai para produção.

### Task 8: Carregar barras e simular carteiras aleatórias por persona

**Files:**
- Create: `research/dispersion_gate.py`
- Test: `tests/test_dispersion_gate.py`

**Interfaces:**
- Consumes: `policy/personas.yaml`
- Produces:
  - `carregar_barras(symbols: list[str], inicio: str, fim: str) -> pd.DataFrame` — colunas = símbolos, índice = data, valores = fechamento ajustado (aqui, e **só aqui**, o ajustado é aceitável: é pesquisa, não registro)
  - `simular_carteira(precos: pd.DataFrame, cfg: dict, seed: int) -> pd.Series` — curva de patrimônio de uma carteira aleatória que respeita `posicao_max_pct`, `posicoes_simultaneas_max` e `caixa_min_pct`
  - `caixa_medio(cfg: dict) -> Decimal` — fração investida máxima implícita nos limites

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_dispersion_gate.py
from decimal import Decimal

import numpy as np
import pandas as pd

from research.dispersion_gate import caixa_medio, simular_carteira


def _precos(n_dias=300, n_ativos=30, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ret = rng.normal(0.0004, 0.015, size=(n_dias, n_ativos))
    precos = 100 * np.exp(np.cumsum(ret, axis=0))
    idx = pd.bdate_range("2024-01-01", periods=n_dias)
    return pd.DataFrame(precos, index=idx, columns=[f"S{i}" for i in range(n_ativos)])


def test_agressivo_fica_no_maximo_40_pct_investido():
    cfg = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5, "caixa_min_pct": "0.00"}
    assert caixa_medio(cfg) == Decimal("0.40")


def test_guardiao_pode_ficar_totalmente_investido():
    cfg = {"posicao_max_pct": "5.00", "posicoes_simultaneas_max": 20, "caixa_min_pct": "0.00"}
    assert caixa_medio(cfg) == Decimal("1.00")


def test_curva_tem_um_ponto_por_dia_e_comeca_em_um():
    p = _precos()
    cfg = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5, "caixa_min_pct": "0.00"}
    curva = simular_carteira(p, cfg, seed=1)
    assert len(curva) == len(p)
    assert abs(curva.iloc[0] - 1.0) < 1e-9


def test_mesma_seed_da_mesma_curva():
    p = _precos()
    cfg = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5, "caixa_min_pct": "0.00"}
    a = simular_carteira(p, cfg, seed=7)
    b = simular_carteira(p, cfg, seed=7)
    pd.testing.assert_series_equal(a, b)


def test_menos_investido_tem_menos_volatilidade():
    p = _precos()
    pouco = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5, "caixa_min_pct": "0.00"}
    muito = {"posicao_max_pct": "5.00", "posicoes_simultaneas_max": 20, "caixa_min_pct": "0.00"}
    vp = simular_carteira(p, pouco, seed=3).pct_change().std()
    vm = simular_carteira(p, muito, seed=3).pct_change().std()
    assert vp < vm
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_dispersion_gate.py -v`
Esperado: FAIL com `ModuleNotFoundError: No module named 'research'`

- [ ] **Step 3: Implementar**

```python
# research/dispersion_gate.py
"""M1 — Gate de Dispersao. Codigo de pesquisa, descartavel.

Pergunta: a dispersao de retorno entre as tres personas vem da FILOSOFIA
ou apenas do nivel de caixa que os limites impoem? Se vier do caixa, o
vencedor de cada temporada e decidido pela direcao do mercado cruzada com
um arquivo de configuracao.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[1]


def carregar_personas() -> dict:
    return yaml.safe_load((RAIZ / "policy" / "personas.yaml").read_text())["personas"]


def caixa_medio(cfg: dict) -> Decimal:
    """Fracao maxima investida implicita nos limites da persona."""
    teto = (Decimal(cfg["posicao_max_pct"]) / Decimal(100)) * Decimal(
        cfg["posicoes_simultaneas_max"]
    )
    piso_caixa = Decimal(cfg["caixa_min_pct"]) / Decimal(100)
    return min(teto, Decimal(1) - piso_caixa)


def carregar_barras(symbols: list[str], inicio: str, fim: str) -> pd.DataFrame:
    import yfinance as yf

    df = yf.download(
        symbols, start=inicio, end=fim, auto_adjust=True, progress=False, group_by="column"
    )
    close = df["Close"] if isinstance(df.columns, pd.MultiIndex) else df[["Close"]]
    return close.dropna(axis=1, how="all").ffill().dropna(how="any")


def simular_carteira(precos: pd.DataFrame, cfg: dict, seed: int) -> pd.Series:
    """Carteira ALEATORIA que respeita os limites da persona.

    Sorteia N ativos com peso igual, rebalanceia mensalmente, e mantem o
    restante em caixa a retorno zero. Zero habilidade por construcao: e
    exatamente esse o ponto.
    """
    rng = np.random.default_rng(seed)
    n = int(cfg["posicoes_simultaneas_max"])
    investido = float(caixa_medio(cfg))

    retornos = precos.pct_change().fillna(0.0)
    # pandas 3.x: .to_period so existe em DatetimeIndex. Um Index comum de
    # datetime.date levanta AttributeError, entao converta explicitamente.
    inicios_de_mes = pd.DatetimeIndex(retornos.index).to_period("M")
    patrimonio = [1.0]
    escolha: list[str] = []
    mes_atual = None

    for data, linha in retornos.iterrows():
        periodo = inicios_de_mes[retornos.index.get_loc(data)]
        if periodo != mes_atual:
            mes_atual = periodo
            k = min(n, precos.shape[1])
            escolha = list(rng.choice(precos.columns, size=k, replace=False))

        ret_cesta = float(linha[escolha].mean()) if escolha else 0.0
        patrimonio.append(patrimonio[-1] * (1.0 + investido * ret_cesta))

    return pd.Series(patrimonio[1:], index=retornos.index, name="patrimonio")
```

- [ ] **Step 4: Rodar até passar**

Run: `uv run pytest tests/test_dispersion_gate.py -v`
Esperado: 5 passed.

- [ ] **Step 5: Commitar**

```bash
git add research/dispersion_gate.py tests/test_dispersion_gate.py
git commit -m "feat(research): simulador de carteira aleatoria por limites de persona"
```

---

### Task 9: Decompor a dispersão e emitir o veredito

**Files:**
- Modify: `research/dispersion_gate.py`
- Create: `reports/dispersion-gate.md` (gerado)
- Test: `tests/test_dispersion_decomposicao.py`

**Interfaces:**
- Consumes: `simular_carteira`, `caixa_medio`, `carregar_barras`
- Produces:
  - `decompor(curvas: dict[str, pd.DataFrame], niveis: dict[str, Decimal]) -> dict` — chaves `r2_caixa`, `dispersao_total_pp`, `dispersao_por_caixa_pp`, `veredito` (`"aprovado"` | `"reprovado"`)
  - `main() -> int` — CLI que baixa dados, roda 2000 amostras por persona, escreve `reports/dispersion-gate.md`

**Critério de decisão, escrito antes de rodar:** se `r2_caixa > 0.80`, o gate **reprova** e as personas são redesenhadas (igualar o caixa-alvo dos três e diferenciar por horizonte e pool de candidatos) antes de qualquer código de produção.

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_dispersion_decomposicao.py
from decimal import Decimal

import numpy as np
import pandas as pd

from research.dispersion_gate import decompor


def _curvas(niveis, ruido, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2024-01-01", periods=260)
    out = {}
    for nome, nivel in niveis.items():
        cols = {}
        for i in range(200):
            ret = rng.normal(0.0005 * float(nivel), 0.01 * float(nivel) + ruido, len(idx))
            cols[i] = np.exp(np.cumsum(ret))
        out[nome] = pd.DataFrame(cols, index=idx)
    return out


def test_reprova_quando_dispersao_vem_do_caixa():
    niveis = {"a": Decimal("0.40"), "b": Decimal("0.85"), "c": Decimal("1.00")}
    r = decompor(_curvas(niveis, ruido=0.0001), niveis)
    assert r["r2_caixa"] > 0.80
    assert r["veredito"] == "reprovado"


def test_aprova_quando_niveis_sao_iguais():
    niveis = {"a": Decimal("0.80"), "b": Decimal("0.80"), "c": Decimal("0.80")}
    r = decompor(_curvas(niveis, ruido=0.02), niveis)
    assert r["r2_caixa"] < 0.80
    assert r["veredito"] == "aprovado"


def test_relatorio_traz_dispersao_em_pontos_percentuais():
    niveis = {"a": Decimal("0.40"), "b": Decimal("1.00")}
    r = decompor(_curvas(niveis, ruido=0.001), niveis)
    assert r["dispersao_total_pp"] > 0
    assert 0.0 <= r["r2_caixa"] <= 1.0
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `uv run pytest tests/test_dispersion_decomposicao.py -v`
Esperado: FAIL com `ImportError: cannot import name 'decompor'`

- [ ] **Step 3: Implementar (acrescentar ao arquivo)**

```python
# research/dispersion_gate.py  (acrescentar ao final)

NASDAQ_TOP = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "AVGO", "GOOGL", "GOOG", "TSLA", "COST",
    "NFLX", "AMD", "PEP", "LIN", "ADBE", "CSCO", "TMUS", "QCOM", "INTU", "AMAT",
    "TXN", "ISRG", "BKNG", "AMGN", "HON", "VRTX", "PANW", "ADP", "SBUX", "GILD",
]
LIMIAR_R2 = 0.80
N_AMOSTRAS = 2000


def decompor(curvas: dict[str, pd.DataFrame], niveis: dict[str, Decimal]) -> dict:
    """Quanto da dispersao entre personas e explicado SO pelo nivel de caixa?

    Regressao do retorno final de cada amostra contra o nivel investido da
    persona que a gerou. R2 alto = o placar mede alocacao, nao habilidade.
    """
    x: list[float] = []
    y: list[float] = []
    finais_por_persona: dict[str, float] = {}

    for nome, df in curvas.items():
        finais = df.iloc[-1].to_numpy(dtype=float) - 1.0
        finais_por_persona[nome] = float(np.mean(finais))
        x.extend([float(niveis[nome])] * len(finais))
        y.extend(finais.tolist())

    xa, ya = np.asarray(x), np.asarray(y)
    if np.std(xa) == 0.0:
        r2 = 0.0
    else:
        r = float(np.corrcoef(xa, ya)[0, 1])
        r2 = r * r

    medias = np.asarray(list(finais_por_persona.values()))
    disp_total = float(medias.max() - medias.min()) * 100.0

    return {
        "r2_caixa": r2,
        "dispersao_total_pp": disp_total,
        "dispersao_por_caixa_pp": disp_total * r2,
        "media_por_persona": finais_por_persona,
        "veredito": "reprovado" if r2 > LIMIAR_R2 else "aprovado",
    }


def main() -> int:
    personas = carregar_personas()
    precos = carregar_barras(NASDAQ_TOP, "2024-07-01", "2026-07-01")
    print(f"barras: {precos.shape[0]} pregoes x {precos.shape[1]} ativos")

    niveis = {n: caixa_medio(cfg) for n, cfg in personas.items()}
    curvas = {
        nome: pd.DataFrame(
            {s: simular_carteira(precos, personas[nome], seed=s) for s in range(N_AMOSTRAS)}
        )
        for nome in personas
    }

    r = decompor(curvas, niveis)

    linhas = [
        "# Gate de Dispersão — M1",
        "",
        f"Universo: {precos.shape[1]} ativos, {precos.shape[0]} pregões "
        f"({precos.index[0].date()} a {precos.index[-1].date()}).",
        f"Amostras aleatórias por persona: {N_AMOSTRAS}.",
        "",
        "## Nível investido implícito nos limites",
        "",
        "| Persona | Investido máx. | Retorno médio da carteira aleatória |",
        "|---|---:|---:|",
    ]
    for nome, nivel in niveis.items():
        linhas.append(
            f"| {nome} | {float(nivel) * 100:.0f}% | "
            f"{r['media_por_persona'][nome] * 100:+.2f}% |"
        )

    linhas += [
        "",
        "## Veredito",
        "",
        f"- Dispersão total entre personas: **{r['dispersao_total_pp']:.2f} p.p.**",
        f"- Fração explicada apenas pelo nível de caixa (R²): "
        f"**{r['r2_caixa'] * 100:.1f}%**",
        f"- Limiar de reprovação declarado antes de rodar: R² > {LIMIAR_R2 * 100:.0f}%",
        "",
        f"### **{r['veredito'].upper()}**",
        "",
    ]
    if r["veredito"] == "reprovado":
        linhas.append(
            "As três carteiras diferem porque têm níveis de caixa diferentes, não porque "
            "têm filosofias diferentes. Redesenhar as personas antes de qualquer código de "
            "produção: igualar o caixa-alvo dos três e diferenciar por horizonte e por pool "
            "de candidatos. Sem isso, o vencedor de cada temporada é decidido pela direção "
            "do mercado cruzada com um arquivo de configuração."
        )
    else:
        linhas.append(
            "O nível de caixa não domina a dispersão. As personas podem seguir como estão, "
            "e a diferença de resultado é atribuível a decisão, não a alocação estrutural."
        )

    destino = RAIZ / "reports" / "dispersion-gate.md"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"\n{destino}\nveredito: {r['veredito']} (R2={r['r2_caixa']:.3f})")
    return 0 if r["veredito"] == "aprovado" else 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Rodar os testes**

Run: `uv run pytest tests/test_dispersion_decomposicao.py -v`
Esperado: 3 passed.

- [ ] **Step 5: Rodar o gate de verdade**

```bash
uv run python research/dispersion_gate.py
cat reports/dispersion-gate.md
```

Leva alguns minutos (2000 amostras × 3 personas). Código de saída 0 = aprovado, 2 = reprovado.

**Se reprovar, pare aqui.** Não avance para M2 antes de redesenhar `policy/personas.yaml` e rodar de novo. Redesenhar agora custa um dia; no mês 8 custaria jogar fora meses de histórico. Registre o resultado em `docs/DECISOES.md`.

- [ ] **Step 6: Commitar**

```bash
git add research/dispersion_gate.py tests/test_dispersion_decomposicao.py reports/
git commit -m "feat(research): decomposicao caixa-vs-selecao e veredito do gate de dispersao"
git push
```

**M1 concluído.** Existe um relatório público que responde se "três filosofias" é premissa real — e o critério estava escrito antes de o número aparecer.

---

## Continuação

M2 (Tasks 10–17: arquivo write-once, conector Alpaca EOD, universo point-in-time, Fiscal de Dados, grade de momentum, ciclo diário, GitHub Actions, painel e verificador em JS) segue em `2026-07-29-m2-o-pulso.md`, escrito ao final desta sessão para manter cada documento em tamanho revisável.

---

## Self-Review

**Cobertura da spec (M0 e M1):** repo público desde o dia 1 → Task 7; MANIFESTO com critérios de fracasso e cláusula de resultado nulo → Task 6; `personas-v1.yaml` → Task 6; `FILL_SPEC` datado antes do simulador → Task 6; contratos em JSON Schema → Task 3; cadeia de hash → Task 4; OpenTimestamps → Task 7; branch protection com `enforce_admins` → Task 7; commits assinados → Task 7; gate de dispersão com critério pré-declarado → Tasks 8–9. Coberto.

**Placeholders:** nenhum "TBD" ou "similar à Task N". As pendências em `docs/DECISOES.md` são decisões do Wilson por design, não lacunas do plano. O golden hash da Task 2 é obtido por comando explícito no Step 4, não deixado em aberto.

**Consistência de tipos:** `caixa_medio` devolve `Decimal` e é consumido como `float(...)` em `simular_carteira` e `decompor` — coerente. `build_entry(session_date, created_at_utc, paths, prev_hash, root)` tem a mesma assinatura na Task 4, no helper de teste e na Task 7. `verify_chain(chain_path, root)` idem. `sha256_hex` recebe dict em todos os usos. `GENESIS_PREV_HASH` importado de `arena.canonical` em ambos os módulos que o usam.

**Um risco conhecido:** a lista `NASDAQ_TOP` da Task 9 é a composição de hoje, o que introduz viés de sobrevivência no gate. É aceitável aqui — o gate mede dispersão estrutural por nível de caixa, não desempenho — e a Task 12 (M2) resolve o problema de verdade, arquivando a composição do QQQ de cada dia. O relatório deve declarar essa limitação.
