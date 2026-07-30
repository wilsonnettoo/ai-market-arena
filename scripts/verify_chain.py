"""Verificador independente da cadeia de hash.

Recomputa a cadeia inteira a partir do genesis e confere o sha256 de cada
arquivo publicado contra os bytes em disco. Nao depende de nada alem do
repositorio: e o comando que qualquer terceiro roda para conferir que a
historia nao foi reescrita.

Uso:
    uv run python scripts/verify_chain.py
    uv run python scripts/verify_chain.py --root . --chain chain/CHAIN.jsonl

Exit 0 = integra. Exit 1 = pelo menos um problema, listado no stdout.
Cadeia inexistente nao e erro: e um repositorio antes do genesis.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arena.audit.chain import read_chain, verify_chain  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="raiz do repositorio")
    ap.add_argument("--chain", default="chain/CHAIN.jsonl", help="caminho da cadeia")
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
