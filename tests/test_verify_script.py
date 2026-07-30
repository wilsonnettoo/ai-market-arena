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
    append_entry(
        chain, build_entry("2026-08-03", "2026-08-03T20:15:00Z", [f], last_hash(chain), tmp)
    )
    return chain


def _roda(tmp: Path, chain: Path) -> subprocess.CompletedProcess:
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


def test_cadeia_inexistente_sai_zero_com_zero_entradas(tmp_path):
    """Repositorio novo, antes do genesis: nao e erro, e ausencia."""
    r = _roda(tmp_path, tmp_path / "chain" / "CHAIN.jsonl")
    assert r.returncode == 0
    assert "0 entradas" in r.stdout


def test_caminho_relativo_resolve_contra_root(tmp_path):
    _monta(tmp_path)
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS: 1 entradas" in r.stdout


def test_roda_no_repositorio_real():
    """O repositorio real ainda nao tem genesis; o verificador nao pode
    explodir por isso — precisa dizer 0 entradas e sair 0."""
    raiz = Path(__file__).resolve().parents[1]
    r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=raiz)
    assert r.returncode == 0, r.stdout + r.stderr
