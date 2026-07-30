from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from research.dispersion_gate import (
    caixa_medio,
    carregar_personas,
    simular_carteira,
)


def _precos(n_dias=300, n_ativos=30, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ret = rng.normal(0.0004, 0.015, size=(n_dias, n_ativos))
    precos = 100 * np.exp(np.cumsum(ret, axis=0))
    idx = pd.bdate_range("2024-01-01", periods=n_dias)
    return pd.DataFrame(precos, index=idx, columns=[f"S{i}" for i in range(n_ativos)])


def test_personas_do_yaml_congelado_sao_tres():
    p = carregar_personas()
    assert set(p) == {"agressivo", "equilibrista", "guardiao"}


def test_agressivo_fica_no_maximo_40_pct_investido():
    cfg = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5, "caixa_min_pct": "0.00"}
    assert caixa_medio(cfg) == Decimal("0.40")


def test_equilibrista_e_limitado_pelo_caixa_minimo_nao_pelo_teto():
    # teto = 8% x 10 = 80%; caixa minimo 15% permitiria 85%. Vence o menor.
    cfg = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 10, "caixa_min_pct": "15.00"}
    assert caixa_medio(cfg) == Decimal("0.80")


def test_guardiao_pode_ficar_totalmente_investido():
    cfg = {"posicao_max_pct": "5.00", "posicoes_simultaneas_max": 20, "caixa_min_pct": "0.00"}
    assert caixa_medio(cfg) == Decimal("1.00")


def test_niveis_reais_do_yaml_confirmam_a_assimetria():
    """O alerta escrito dentro de policy/personas.yaml precisa ser verdade."""
    p = carregar_personas()
    niveis = {n: caixa_medio(cfg) for n, cfg in p.items()}
    assert niveis["agressivo"] == Decimal("0.40")
    assert niveis["equilibrista"] == Decimal("0.80")
    assert niveis["guardiao"] == Decimal("1.00")


def test_curva_tem_um_ponto_por_dia_e_comeca_perto_de_um():
    p = _precos()
    cfg = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5, "caixa_min_pct": "0.00"}
    curva = simular_carteira(p, cfg, seed=1)
    assert len(curva) == len(p)
    assert abs(curva.iloc[0] - 1.0) < 0.05


def test_mesma_seed_da_mesma_curva():
    p = _precos()
    cfg = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5, "caixa_min_pct": "0.00"}
    pd.testing.assert_series_equal(
        simular_carteira(p, cfg, seed=7), simular_carteira(p, cfg, seed=7)
    )


def test_seeds_diferentes_dao_curvas_diferentes():
    p = _precos()
    cfg = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5, "caixa_min_pct": "0.00"}
    a = simular_carteira(p, cfg, seed=1)
    b = simular_carteira(p, cfg, seed=2)
    assert not np.allclose(a.to_numpy(), b.to_numpy())


def test_menos_investido_tem_menos_volatilidade():
    """O nucleo da hipotese do gate: nivel de caixa move a volatilidade
    sozinho, sem nenhuma diferenca de habilidade."""
    p = _precos()
    pouco = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5, "caixa_min_pct": "0.00"}
    muito = {"posicao_max_pct": "5.00", "posicoes_simultaneas_max": 20, "caixa_min_pct": "0.00"}
    vp = simular_carteira(p, pouco, seed=3).pct_change().std()
    vm = simular_carteira(p, muito, seed=3).pct_change().std()
    assert vp < vm


def test_indice_de_datas_puras_nao_quebra():
    """pandas 3.x: Index.to_period so existe em DatetimeIndex. Se a
    implementacao nao converter, isto levanta AttributeError."""
    p = _precos(n_dias=120)
    p.index = [d.date() for d in p.index]
    cfg = {"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5, "caixa_min_pct": "0.00"}
    curva = simular_carteira(p, cfg, seed=1)
    assert len(curva) == 120


def test_universo_menor_que_o_numero_de_posicoes_nao_quebra():
    p = _precos(n_ativos=3)
    cfg = {"posicao_max_pct": "5.00", "posicoes_simultaneas_max": 20, "caixa_min_pct": "0.00"}
    assert len(simular_carteira(p, cfg, seed=1)) == len(p)


def test_caixa_minimo_acima_de_cem_por_cento_e_rejeitado():
    with pytest.raises(ValueError):
        caixa_medio({"posicao_max_pct": "8.00", "posicoes_simultaneas_max": 5,
                     "caixa_min_pct": "120.00"})
