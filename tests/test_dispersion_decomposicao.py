from decimal import Decimal

import numpy as np
import pytest

from research.dispersion_gate import LIMIAR_CONCORDANCIA, decompor

NIVEIS = {"agressivo": Decimal("0.40"), "equilibrista": Decimal("0.80"),
          "guardiao": Decimal("1.00")}


def _pareado(mercado: np.ndarray, ruido: float, seed: int = 0) -> dict[str, np.ndarray]:
    """Cada corrida i ve o MESMO retorno de mercado para as tres personas.

    O retorno de cada persona e exposicao * mercado + ruido idiossincratico.
    `ruido` alto simula selecao de acoes com muita dispersao; `ruido` zero
    simula um mundo onde so a exposicao importa.
    """
    rng = np.random.default_rng(seed)
    return {
        nome: float(nivel) * mercado + rng.normal(0, ruido, len(mercado))
        for nome, nivel in NIVEIS.items()
    }


def test_reprova_quando_so_a_exposicao_importa():
    """Mercado sempre positivo e zero ruido: o mais exposto vence sempre."""
    mercado = np.full(1000, 0.10)
    r = decompor(_pareado(mercado, ruido=0.0), NIVEIS)
    assert r["concordancia_com_exposicao"] == 1.0
    assert r["veredito"] == "reprovado"


def test_reprova_tambem_em_mercado_de_baixa():
    """Ranking invertido tambem significa placar decidido pela exposicao."""
    mercado = np.full(1000, -0.10)
    r = decompor(_pareado(mercado, ruido=0.0), NIVEIS)
    assert r["concordancia_com_exposicao"] == 1.0
    assert r["veredito"] == "reprovado"
    assert r["vitorias_da_mais_exposta"] == 0.0  # em baixa, o mais exposto perde


def test_aprova_quando_a_selecao_domina():
    """Ruido idiossincratico grande: qual persona vence depende do sorteio."""
    rng = np.random.default_rng(1)
    mercado = rng.normal(0.0, 0.15, 2000)
    r = decompor(_pareado(mercado, ruido=0.40, seed=2), NIVEIS)
    assert r["concordancia_com_exposicao"] < LIMIAR_CONCORDANCIA
    assert r["veredito"] == "aprovado"


def test_sob_acaso_puro_a_concordancia_fica_perto_de_um_terco():
    """Baseline: sem nenhum efeito de exposicao, 2 de 6 ordenacoes coincidem."""
    rng = np.random.default_rng(3)
    finais = {n: rng.normal(0, 1, 20000) for n in NIVEIS}
    r = decompor(finais, NIVEIS)
    assert abs(r["concordancia_com_exposicao"] - 1 / 3) < 0.02
    assert r["esperado_sob_acaso"] == pytest.approx(1 / 3)
    assert r["veredito"] == "aprovado"


def test_ordem_de_exposicao_e_do_maior_para_o_menor():
    r = decompor(_pareado(np.full(10, 0.1), ruido=0.0), NIVEIS)
    assert r["ordem_de_exposicao"] == ("guardiao", "equilibrista", "agressivo")


def test_corridas_nao_pareadas_sao_rejeitadas():
    with pytest.raises(ValueError, match="pareadas"):
        decompor({"a": np.zeros(10), "b": np.zeros(5)},
                 {"a": Decimal("0.5"), "b": Decimal("1.0")})


def test_uma_persona_so_e_rejeitada():
    with pytest.raises(ValueError, match="duas personas"):
        decompor({"a": np.zeros(10)}, {"a": Decimal("0.5")})


def test_limiar_esta_declarado_antes_de_rodar():
    """O criterio de reprovacao e parte do pre-registro: se pudesse ser
    escolhido depois de ver o numero, o gate nao valeria nada."""
    assert LIMIAR_CONCORDANCIA == 0.80


def test_metrica_antiga_por_r2_seria_vazia():
    """Guarda de regressao contra voltar ao R2 (ver D20).

    No cenario que DEVE reprovar — so a exposicao importa — o R2 do retorno
    final contra o nivel investido tambem e alto. Mas no cenario realista, com
    selecao de acoes dispersando os resultados, ele desaba para perto de zero
    enquanto a concordancia ainda detecta o problema. Este teste fixa esse fato.
    """
    mercado = np.full(3000, 0.10)
    finais = _pareado(mercado, ruido=0.25, seed=8)

    x = np.concatenate([np.full(len(v), float(NIVEIS[n])) for n, v in finais.items()])
    y = np.concatenate([v for v in finais.values()])
    r2 = float(np.corrcoef(x, y)[0, 1]) ** 2

    conc = decompor(finais, NIVEIS)["concordancia_com_exposicao"]
    assert r2 < 0.20, f"R2={r2:.3f} — se subiu, o cenario mudou"
    assert conc > r2, "a concordancia precisa detectar o que o R2 nao detecta"
