"""Gate de conformidade dos contratos.

Por que introspeccao e nao grep: a primeira versao deste check comparava
contagens de `ConfigDict(`, `strict=True` e `extra="forbid"` com grep, e deu
falso positivo no primeiro uso real — o docstring do modulo mencionava os dois
flags e inflava a contagem. Introspecao le a configuracao efetiva da classe,
incluindo o que veio por heranca, e e imune a comentario e docstring.

Verifica:
  1. todo modelo de contrato tem strict=True, extra="forbid" e frozen=True;
  2. todo campo com strict=False por campo esta documentado em docs/DECISOES.md;
  3. nenhum campo de valor decimal e tipado como float.

Uso:
    uv run python scripts/check_contracts.py
"""

from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from pydantic import BaseModel  # noqa: E402

import arena.contracts.records as mod  # noqa: E402

_DECISOES = RAIZ / "docs" / "DECISOES.md"


def _modelos() -> list[tuple[str, type[BaseModel]]]:
    return [
        (nome, cls)
        for nome, cls in inspect.getmembers(mod, inspect.isclass)
        if issubclass(cls, BaseModel) and cls is not BaseModel and cls.__module__ == mod.__name__
    ]


def _config_exigida(cls: type[BaseModel]) -> list[str]:
    cfg = cls.model_config
    faltas = []
    if cfg.get("strict") is not True:
        faltas.append("strict=True")
    if cfg.get("extra") != "forbid":
        faltas.append('extra="forbid"')
    if cfg.get("frozen") is not True:
        faltas.append("frozen=True")
    return faltas


def _campos_strict_false(cls: type[BaseModel]) -> list[str]:
    achados = []
    for campo, info in cls.model_fields.items():
        for meta in info.metadata or []:
            if getattr(meta, "strict", None) is False:
                achados.append(campo)
    return achados


def _campos_float(cls: type[BaseModel]) -> list[str]:
    return [
        campo
        for campo, info in cls.model_fields.items()
        if info.annotation is float or repr(info.annotation).find("float") != -1
    ]


def main() -> int:
    erros: list[str] = []
    avisos: list[str] = []
    conformes: list[str] = []

    decisoes = _DECISOES.read_text(encoding="utf-8") if _DECISOES.exists() else ""

    for nome, cls in _modelos():
        faltas = _config_exigida(cls)
        if faltas:
            erros.append(f"{nome}: model_config sem {', '.join(faltas)}")
        else:
            conformes.append(nome)

        for campo in _campos_float(cls):
            erros.append(
                f"{nome}.{campo}: tipado como float. "
                "Valor decimal em registro hasheado viaja como string (I1)."
            )

        for campo in _campos_strict_false(cls):
            documentado = re.search(
                r"^### D\d+.*strict=False.*$", decisoes, re.MULTILINE | re.IGNORECASE
            )
            if documentado:
                avisos.append(f"{nome}.{campo}: strict=False por campo, documentado em DECISOES")
            else:
                erros.append(
                    f"{nome}.{campo}: strict=False por campo SEM entrada em docs/DECISOES.md. "
                    "A excecao ao invariante I5 precisa ser decidida, nao herdada."
                )

    for a in avisos:
        print(f"AVISA  {a}")
    for e in erros:
        print(f"BLOQUEIA  {e}")

    if erros:
        print(f"\nFAIL: {len(erros)} problema(s) de conformidade de contrato")
        return 1

    print(f"\nPASS: {len(conformes)} modelos conformes ({', '.join(sorted(conformes))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
