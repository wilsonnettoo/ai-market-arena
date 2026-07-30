"""O gate de contratos precisa passar no codigo real E pegar violacao real.

Um gate que so sabe dizer PASS e indistinguivel de um gate quebrado.
"""

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "scripts" / "check_contracts.py"
RECORDS = RAIZ / "arena" / "contracts" / "records.py"


def _roda() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=RAIZ
    )


def test_codigo_real_passa():
    r = _roda()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS:" in r.stdout


def test_strict_false_por_campo_e_reportado_como_aviso():
    r = _roda()
    assert "AVISA" in r.stdout
    assert "persona" in r.stdout


def test_pega_config_sem_strict(tmp_path):
    original = RECORDS.read_text(encoding="utf-8")
    try:
        RECORDS.write_text(
            original.replace(
                'model_config = ConfigDict(extra="forbid", frozen=True, strict=True)',
                'model_config = ConfigDict(extra="forbid", frozen=True)',
            ),
            encoding="utf-8",
        )
        r = _roda()
        assert r.returncode == 1
        assert "model_config sem strict=True" in r.stdout
    finally:
        RECORDS.write_text(original, encoding="utf-8")


def test_pega_campo_tipado_como_float():
    original = RECORDS.read_text(encoding="utf-8")
    try:
        RECORDS.write_text(
            original.replace("    p_up: DecimalStr", "    p_up: float"), encoding="utf-8"
        )
        r = _roda()
        assert r.returncode == 1
        assert "tipado como float" in r.stdout
    finally:
        RECORDS.write_text(original, encoding="utf-8")


def test_restaurou_o_arquivo_original():
    """Guarda contra teste destrutivo que vaza estado."""
    r = _roda()
    assert r.returncode == 0
