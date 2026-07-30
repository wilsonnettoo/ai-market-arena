"""Cadeia de hash append-only.

Cada entrada carrega o hash da anterior. Editar, remover ou reordenar qualquer
arquivo ja registrado quebra a verificacao — que e exatamente a propriedade que
"PostgreSQL imutavel" e "commit no GitHub" nao dao: voce e superusuario do banco,
e a data de autoria de um commit e um campo que o autor escolhe.

Duas decisoes de desenho que parecem detalhe e nao sao:

  1. `file_sha256` hasheia os BYTES EM DISCO, nao a forma canonica. O arquivo
     publicado pode ter qualquer formatacao; o que a cadeia promete e que
     aqueles bytes especificos nao mudaram.

  2. `entry_hash` e o hash do dict SEM a propria chave `entry_hash`. Incluir-se
     no proprio calculo tornaria impossivel recomputa-lo, e o verificador que
     roda no navegador do visitante nao conseguiria conferir nada.
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
        (
            {"path": str(p.relative_to(root).as_posix()), "sha256": file_sha256(p)}
            for p in paths
        ),
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
    # modo "ab": append puro. Reabrir em "w" em qualquer ponto do codigo
    # destruiria a cadeia inteira sem deixar rastro.
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
    """Devolve a lista de erros. Vazia significa cadeia integra.

    Nao levanta excecao de proposito: o chamador precisa poder relatar TODOS os
    problemas, nao parar no primeiro.
    """
    erros: list[str] = []
    esperado_prev = GENESIS_PREV_HASH

    for i, entrada in enumerate(read_chain(chain_path)):
        rotulo = f"linha {i + 1} ({entrada.get('session_date', '?')})"

        corpo = {k: v for k, v in entrada.items() if k != "entry_hash"}
        if sha256_hex(corpo) != entrada.get("entry_hash"):
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
