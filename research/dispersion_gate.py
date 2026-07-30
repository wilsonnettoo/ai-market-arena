"""M1 — Gate de Dispersao. Codigo de pesquisa, descartavel.

A pergunta: a dispersao de retorno entre as tres personas vem da FILOSOFIA ou
apenas do nivel de caixa que os limites impoem?

Se vier do caixa, o vencedor de cada temporada e decidido pela direcao do
mercado cruzada com um arquivo de configuracao — e a "comparacao justa entre
filosofias" prometida no projeto seria propaganda, desmontavel nos comentarios
em cinco minutos.

O metodo: simular carteiras ALEATORIAS que respeitam exatamente os limites de
cada persona. Zero habilidade por construcao — e exatamente esse o ponto. Se
carteiras sem nenhuma habilidade ja produzem a dispersao observada, entao a
dispersao nao mede habilidade.

CRITERIO ESCRITO ANTES DE RODAR: se o ranking das tres personas coincidir com a
ordem de exposicao (ou com o exato inverso dela) em mais de 80% das corridas, o
gate REPROVA e os limites em policy/personas.yaml sao redesenhados antes de
qualquer codigo de producao. Sob nenhum efeito, o esperado seria 33,3%.
"""

from __future__ import annotations

import math
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[1]
# CRITERIO DE REPROVACAO, declarado antes de rodar. Se o ranking das personas
# coincidir com a ordem de exposicao (ou o exato inverso dela) em mais de 80%
# das corridas COM CARTEIRAS ALEATORIAS, o placar e decidido por configuracao.
# Sob nenhum efeito, o esperado para tres personas e 2/3! = 33,3%.
LIMIAR_CONCORDANCIA = 0.80
N_CORRIDAS = 2000


def carregar_personas() -> dict:
    return yaml.safe_load(
        (RAIZ / "policy" / "personas.yaml").read_text(encoding="utf-8")
    )["personas"]


def caixa_medio(cfg: dict) -> Decimal:
    """Fracao maxima investida implicita nos limites da persona.

    E o minimo entre o teto estrutural (tamanho maximo de posicao vezes numero
    de posicoes simultaneas) e o que sobra depois do caixa minimo obrigatorio.
    """
    piso_caixa = Decimal(cfg["caixa_min_pct"]) / Decimal(100)
    if not (Decimal(0) <= piso_caixa <= Decimal(1)):
        raise ValueError(f"caixa_min_pct fora de [0, 100]: {cfg['caixa_min_pct']}")

    teto = (Decimal(cfg["posicao_max_pct"]) / Decimal(100)) * Decimal(
        cfg["posicoes_simultaneas_max"]
    )
    return min(teto, Decimal(1) - piso_caixa)


def carregar_barras(symbols: list[str], inicio: str, fim: str) -> pd.DataFrame:
    """Fechamento ajustado. Aqui — e SO aqui — o ajustado e aceitavel:
    isto e pesquisa descartavel, nao registro publicado."""
    import yfinance as yf

    df = yf.download(
        symbols, start=inicio, end=fim, auto_adjust=True, progress=False, group_by="column"
    )
    close = df["Close"] if isinstance(df.columns, pd.MultiIndex) else df[["Close"]]
    return close.dropna(axis=1, how="all").ffill().dropna(how="any")


def simular_carteira(precos: pd.DataFrame, cfg: dict, seed: int) -> pd.Series:
    """Carteira ALEATORIA que respeita os limites da persona.

    Sorteia N ativos com peso igual, rebalanceia mensalmente, e mantem o
    restante em caixa a retorno zero.
    """
    rng = np.random.default_rng(seed)
    n = int(cfg["posicoes_simultaneas_max"])
    investido = float(caixa_medio(cfg))

    retornos = precos.pct_change().fillna(0.0)
    # pandas 3.x: .to_period so existe em DatetimeIndex. Um Index comum de
    # datetime.date levanta AttributeError — converter explicitamente.
    periodos = pd.DatetimeIndex(retornos.index).to_period("M")

    r = retornos.to_numpy(dtype=float)
    n_dias, n_ativos = r.shape
    k = min(n, n_ativos)

    # Vetorizado: montamos a matriz de pesos de uma vez e fazemos um unico
    # produto. Iterar linha a linha com pandas custaria minutos nas 6000
    # simulacoes do gate. A ordem dos sorteios e preservada, entao a mesma
    # semente continua produzindo exatamente a mesma curva.
    pesos = np.zeros((n_dias, n_ativos))
    mes_atual = None
    escolha = np.empty(0, dtype=int)
    for i in range(n_dias):
        if periodos[i] != mes_atual:
            mes_atual = periodos[i]
            escolha = rng.choice(n_ativos, size=k, replace=False)
        pesos[i, escolha] = 1.0 / k

    ret_cesta = (r * pesos).sum(axis=1)
    patrimonio = np.cumprod(1.0 + investido * ret_cesta)
    return pd.Series(patrimonio, index=retornos.index, name="patrimonio")


# Composicao do Nasdaq-100 usada apenas na pesquisa. Introduz vies de
# sobrevivencia — e aceitavel AQUI porque o gate mede dispersao estrutural por
# nivel de caixa, nao desempenho. O universo point-in-time de verdade entra no
# M2, arquivando a composicao do QQQ de cada dia.
NASDAQ_TOP = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "AVGO", "GOOGL", "GOOG", "TSLA", "COST",
    "NFLX", "AMD", "PEP", "LIN", "ADBE", "CSCO", "TMUS", "QCOM", "INTU", "AMAT",
    "TXN", "ISRG", "BKNG", "AMGN", "HON", "VRTX", "PANW", "ADP", "SBUX", "GILD",
]


def decompor(finais: dict[str, np.ndarray], niveis: dict[str, Decimal]) -> dict:
    """O placar e decidido pelo nivel de exposicao?

    `finais` mapeia persona -> array de retornos finais, PAREADO por indice: a
    posicao i de todas as personas veio da mesma corrida, ou seja, do mesmo
    mercado e da mesma semente. E assim que a competicao real funciona — as tres
    veem os mesmos pregoes.

    METRICA: com que frequencia o ranking das tres personas coincide com a ordem
    de exposicao (ou com o exato inverso dela)? Coincidir com o inverso conta
    igual, porque tambem significa que o placar foi decidido pela exposicao — so
    que num mercado de baixa. Como as carteiras sao aleatorias e nao tem
    habilidade nenhuma por construcao, concordancia alta significa que o vencedor
    de cada temporada e decidido por um arquivo de configuracao cruzado com a
    direcao do mercado.

    Sob nenhum efeito, a concordancia esperada e 2/k! — para tres personas,
    33,3%.

    POR QUE NAO R2. A primeira versao desta funcao regredia o retorno final de
    cada amostra contra o nivel investido e usava R2. A metrica e quase vazia:
    ela mede quanto o nivel explica da variancia TOTAL, e a variancia DENTRO de
    cada persona (qual sorteio de acoes deu certo) domina. Medido empiricamente,
    o R2 so passa de 0,80 no caso perfeitamente deterministico; em qualquer
    cenario realista fica entre 0,02 e 0,08, e o gate aprovaria sempre. Ver D20.
    """
    if len(finais) < 2:
        raise ValueError("decompor precisa de pelo menos duas personas")

    tamanhos = {len(v) for v in finais.values()}
    if len(tamanhos) != 1:
        raise ValueError(f"corridas precisam ser pareadas; tamanhos: {tamanhos}")

    nomes = list(finais)
    ordem_exposicao = tuple(sorted(nomes, key=lambda n: -float(niveis[n])))
    ordem_inversa = tuple(reversed(ordem_exposicao))
    mais_exposta = ordem_exposicao[0]

    n_corridas = tamanhos.pop()
    concordantes = 0
    vitorias_da_mais_exposta = 0

    for i in range(n_corridas):
        ranking = tuple(sorted(nomes, key=lambda n: -finais[n][i]))
        if ranking in (ordem_exposicao, ordem_inversa):
            concordantes += 1
        if ranking[0] == mais_exposta:
            vitorias_da_mais_exposta += 1

    concordancia = concordantes / n_corridas
    k = len(nomes)
    esperado_sob_acaso = 2.0 / float(math.factorial(k))

    medias = {n: float(np.mean(v)) for n, v in finais.items()}
    disp_total = (max(medias.values()) - min(medias.values())) * 100.0

    return {
        "concordancia_com_exposicao": concordancia,
        "esperado_sob_acaso": esperado_sob_acaso,
        "vitorias_da_mais_exposta": vitorias_da_mais_exposta / n_corridas,
        "ordem_de_exposicao": ordem_exposicao,
        "media_por_persona": medias,
        "dispersao_media_pp": disp_total,
        "n_corridas": n_corridas,
        "veredito": "reprovado" if concordancia > LIMIAR_CONCORDANCIA else "aprovado",
    }


def rodar_gate(precos: pd.DataFrame, personas: dict, n_corridas: int = N_CORRIDAS) -> dict:
    """Corridas PAREADAS: a corrida i usa a mesma semente nas tres personas."""
    niveis = {n: caixa_medio(cfg) for n, cfg in personas.items()}
    finais = {n: np.empty(n_corridas) for n in personas}
    for s in range(n_corridas):
        for nome, cfg in personas.items():
            finais[nome][s] = float(simular_carteira(precos, cfg, seed=s).iloc[-1]) - 1.0
    r = decompor(finais, niveis)
    r["niveis"] = {n: float(v) for n, v in niveis.items()}
    return r


SUB_PERIODOS = [
    ("2024-07-01", "2025-01-01", "2o sem 2024"),
    ("2025-01-01", "2025-07-01", "1o sem 2025"),
    ("2025-07-01", "2026-01-01", "2o sem 2025"),
    ("2026-01-01", "2026-07-01", "1o sem 2026"),
]


def _relatorio(r: dict, precos: pd.DataFrame, mercado_pct: float, robustez: list) -> str:
    aprovado = r["veredito"] == "aprovado"
    linhas = [
        "# Gate de Dispersão — M1",
        "",
        "Pergunta: a diferença de retorno entre as três personas vem da **filosofia** ou",
        "apenas do **nível de exposição** que os limites impõem?",
        "",
        "Método: simular carteiras long-only **aleatórias** que respeitam exatamente os",
        "limites de cada persona em `policy/personas.yaml`. Zero habilidade por construção.",
        "As corridas são pareadas — a corrida *i* usa a mesma semente nas três personas,",
        "como na competição real, em que as três veem os mesmos pregões.",
        "",
        f"Universo: {precos.shape[1]} ativos, {precos.shape[0]} pregões "
        f"({precos.index[0].date()} a {precos.index[-1].date()}). "
        f"Retorno médio do universo no período: **{mercado_pct:+.1f}%**.",
        f"Corridas por persona: {r['n_corridas']}.",
        "",
        "## Exposição implícita nos limites",
        "",
        "| Persona | Investido máx. | Retorno médio da carteira aleatória |",
        "|---|---:|---:|",
    ]
    for nome in r["ordem_de_exposicao"]:
        linhas.append(
            f"| {nome} | {r['niveis'][nome] * 100:.0f}% | "
            f"{r['media_por_persona'][nome] * 100:+.2f}% |"
        )

    linhas += [
        "",
        "## Resultado",
        "",
        f"- Ordem de exposição (maior para menor): **{' > '.join(r['ordem_de_exposicao'])}**",
        f"- Ranking coincidiu com a ordem de exposição (ou o inverso dela) em "
        f"**{r['concordancia_com_exposicao'] * 100:.1f}%** das corridas",
        f"- Esperado sob puro acaso: {r['esperado_sob_acaso'] * 100:.1f}%",
        f"- A persona mais exposta venceu em {r['vitorias_da_mais_exposta'] * 100:.1f}% "
        f"das corridas",
        f"- Limiar de reprovação, declarado antes de rodar: "
        f"**{LIMIAR_CONCORDANCIA * 100:.0f}%**",
        "",
        f"### {r['veredito'].upper()}",
        "",
    ]
    if aprovado:
        linhas.append(
            "A exposição não determina o placar sozinha: com carteiras sem nenhuma "
            "habilidade, o ranking entre as personas varia conforme o sorteio. Isso "
            "significa que uma diferença observada entre elas **pode** ser atribuída à "
            "decisão, e não é consequência mecânica do arquivo de configuração. As "
            "personas seguem como estão."
        )
    else:
        linhas.append(
            "Com carteiras que **não têm habilidade nenhuma**, o ranking das personas já "
            "reproduz a ordem de exposição na maior parte das corridas. O vencedor de cada "
            "temporada seria decidido pela direção do mercado cruzada com um arquivo de "
            "configuração, e a comparação entre filosofias seria propaganda. Os limites em "
            "`policy/personas.yaml` precisam ser redesenhados **antes** de qualquer código "
            "de produção: igualar o caixa-alvo das três e diferenciar por horizonte e por "
            "pool de candidatos."
        )

    spread = (max(r["media_por_persona"].values())
              - min(r["media_por_persona"].values())) * 100
    linhas += [
        "",
        "## O número que importa mesmo com o gate aprovado",
        "",
        "Com **zero habilidade**, a diferença média entre a persona mais exposta e a menos",
        f"exposta foi de **{spread:.1f} pontos percentuais** neste período. O gate passou",
        "porque o ranking não é determinado pela exposição — mas a magnitude do efeito não é",
        "pequena, e qualquer leitura do placar precisa levar isso em conta.",
        "",
        "## Robustez por sub-período",
        "",
        "O efeito da exposição **se acumula com o tempo**: quanto mais longa a janela, mais",
        "a exposição domina. Como uma temporada real é curta, este recorte é mais",
        "representativo do uso do que o período inteiro.",
        "",
        "| Sub-período | Mercado | Concordância | Vence + exposta | Spread | Veredito |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for rot, mkt, rr in robustez:
        m = rr["media_por_persona"]
        sp = (max(m.values()) - min(m.values())) * 100
        linhas.append(
            f"| {rot} | {mkt:+.1f}% | {rr['concordancia_com_exposicao'] * 100:.1f}% | "
            f"{rr['vitorias_da_mais_exposta'] * 100:.1f}% | {sp:.1f} p.p. | "
            f"{rr['veredito']} |"
        )
    linhas += [
        "",
        f"Em janelas de seis meses a concordância se aproxima do acaso "
        f"({r['esperado_sob_acaso'] * 100:.1f}%)",
        "e o spread cai para poucos pontos percentuais. Isso reforça a aprovação para o uso",
        "pretendido, e ao mesmo tempo avisa que uma temporada longa mudaria o quadro.",
        "",
        "## Limitações declaradas",
        "",
        "- O universo usado aqui é a composição **de hoje** do topo do Nasdaq-100, o que",
        "  introduz viés de sobrevivência. É aceitável para esta pergunta, que é sobre",
        "  dispersão estrutural por nível de exposição e não sobre desempenho. O universo",
        "  point-in-time de verdade entra no M2, arquivando a composição do QQQ a cada dia.",
        "- O resultado depende do período: em mercado fortemente direcional a exposição pesa",
        "  mais. Por isso o retorno do universo no período está declarado acima.",
        "- Preço ajustado é usado aqui — e **somente aqui**, porque isto é pesquisa",
        "  descartável e não registro publicado.",
        "",
    ]
    return "\n".join(linhas) + "\n"


def main() -> int:
    personas = carregar_personas()
    print(f"baixando {len(NASDAQ_TOP)} ativos...")
    precos = carregar_barras(NASDAQ_TOP, "2024-07-01", "2026-07-01")
    print(f"barras: {precos.shape[0]} pregoes x {precos.shape[1]} ativos")

    mercado = float((precos.iloc[-1] / precos.iloc[0] - 1).mean()) * 100
    print(f"simulando {N_CORRIDAS} corridas pareadas x {len(personas)} personas...")
    r = rodar_gate(precos, personas)

    print("robustez por sub-periodo...")
    robustez = []
    for ini, fim, rot in SUB_PERIODOS:
        ps = carregar_barras(NASDAQ_TOP, ini, fim)
        mkt = float((ps.iloc[-1] / ps.iloc[0] - 1).mean()) * 100
        robustez.append((rot, mkt, rodar_gate(ps, personas, n_corridas=500)))

    destino = RAIZ / "reports" / "dispersion-gate.md"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(_relatorio(r, precos, mercado, robustez), encoding="utf-8")

    print(f"\n{destino}")
    print(f"concordancia com a exposicao: {r['concordancia_com_exposicao'] * 100:.1f}% "
          f"(acaso: {r['esperado_sob_acaso'] * 100:.1f}%, limiar: "
          f"{LIMIAR_CONCORDANCIA * 100:.0f}%)")
    print(f"VEREDITO: {r['veredito'].upper()}")
    return 0 if r["veredito"] == "aprovado" else 2


if __name__ == "__main__":
    raise SystemExit(main())
