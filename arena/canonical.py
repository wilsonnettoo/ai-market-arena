"""Forma canonica de serializacao e hash.

Contrato congelado. Qualquer mudanca aqui invalida toda a cadeia ja publicada,
portanto exige nova temporada e entrada em docs/DECISOES.md.

Regras:
  - chaves ordenadas, sem espacos, UTF-8 literal (sem escape ASCII);
  - floats sao PROIBIDOS: nao possuem forma canonica reproduzivel entre
    Python e JavaScript, e o verificador do navegador precisa recomputar
    exatamente o mesmo hash. Numeros decimais viajam como string.

Este modulo e normativo. Quando site/verify.js divergir dele, corrija o
JavaScript — nunca o contrario.
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
