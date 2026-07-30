"""Contratos congelados.

Mudanca exige bump de SCHEMA_VERSION, migracao das fixtures douradas e entrada
em docs/DECISOES.md. O CI reprova diff aqui sem diff correspondente lá.

Tres invariantes moram nas anotacoes, nao em prosa:
  - todo valor decimal e DecimalStr (string com ponto), nunca float — I1;
  - todo timestamp e UtcStamp terminando em Z — I2;
  - strict=True e extra="forbid" em _Record: rejeicao, nunca coercao — I5.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from arena.canonical import sha256_hex

SCHEMA_VERSION = "1.0.0"

_UTC_Z = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
_DATE = r"^\d{4}-\d{2}-\d{2}$"
_SHA256 = r"^[0-9a-f]{64}$"
_DECIMAL = r"^-?\d+\.\d+$"

DecimalStr = Annotated[str, Field(pattern=_DECIMAL)]
UtcStamp = Annotated[str, Field(pattern=_UTC_Z)]
SessionDate = Annotated[str, Field(pattern=_DATE)]
Sha256Hex = Annotated[str, Field(pattern=_SHA256)]


class Persona(StrEnum):
    # O nome editorial do agressivo esta pendente em docs/DECISOES.md D10.
    # O identificador tecnico e estavel e nao muda com a decisao editorial.
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
    # strict=False APENAS aqui, e por um motivo estrutural: com strict global,
    # pydantic recusa a string "agressivo" de volta para o membro do enum, e o
    # registro publicado deixa de ser legivel pelo sistema que o produziu — o
    # resolvedor e o painel LEEM os JSON publicados. Aceitar exatamente um dos
    # tres valores declarados nao e coercao no sentido que o invariante I5
    # proibe: valor fora do enum continua rejeitado, e strict segue valendo em
    # todos os outros campos (float em p_up ainda e recusado). Ver D19.
    persona: Annotated[Persona, Field(strict=False)]
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
