# Gate de Dispersão — M1

Pergunta: a diferença de retorno entre as três personas vem da **filosofia** ou
apenas do **nível de exposição** que os limites impõem?

Método: simular carteiras long-only **aleatórias** que respeitam exatamente os
limites de cada persona em `policy/personas.yaml`. Zero habilidade por construção.
As corridas são pareadas — a corrida *i* usa a mesma semente nas três personas,
como na competição real, em que as três veem os mesmos pregões.

Universo: 30 ativos, 501 pregões (2024-07-01 a 2026-06-30). Retorno médio do universo no período: **+47.4%**.
Corridas por persona: 2000.

## Exposição implícita nos limites

| Persona | Investido máx. | Retorno médio da carteira aleatória |
|---|---:|---:|
| guardiao | 100% | +44.28% |
| equilibrista | 80% | +34.68% |
| agressivo | 40% | +16.58% |

## Resultado

- Ordem de exposição (maior para menor): **guardiao > equilibrista > agressivo**
- Ranking coincidiu com a ordem de exposição (ou o inverso dela) em **61.3%** das corridas
- Esperado sob puro acaso: 33.3%
- A persona mais exposta venceu em 72.4% das corridas
- Limiar de reprovação, declarado antes de rodar: **80%**

### APROVADO

A exposição não determina o placar sozinha: com carteiras sem nenhuma habilidade, o ranking entre as personas varia conforme o sorteio. Isso significa que uma diferença observada entre elas **pode** ser atribuída à decisão, e não é consequência mecânica do arquivo de configuração. As personas seguem como estão.

## O número que importa mesmo com o gate aprovado

Com **zero habilidade**, a diferença média entre a persona mais exposta e a menos
exposta foi de **27.7 pontos percentuais** neste período. O gate passou
porque o ranking não é determinado pela exposição — mas a magnitude do efeito não é
pequena, e qualquer leitura do placar precisa levar isso em conta.

## Robustez por sub-período

O efeito da exposição **se acumula com o tempo**: quanto mais longa a janela, mais
a exposição domina. Como uma temporada real é curta, este recorte é mais
representativo do uso do que o período inteiro.

| Sub-período | Mercado | Concordância | Vence + exposta | Spread | Veredito |
|---|---:|---:|---:|---:|---|
| 2o sem 2024 | +9.4% | 43.2% | 63.6% | 5.1 p.p. | aprovado |
| 1o sem 2025 | +9.1% | 45.2% | 58.8% | 6.1 p.p. | aprovado |
| 2o sem 2025 | +9.5% | 40.2% | 60.4% | 5.6 p.p. | aprovado |
| 1o sem 2026 | +15.6% | 37.8% | 57.0% | 7.3 p.p. | aprovado |

Em janelas de seis meses a concordância se aproxima do acaso (33.3%)
e o spread cai para poucos pontos percentuais. Isso reforça a aprovação para o uso
pretendido, e ao mesmo tempo avisa que uma temporada longa mudaria o quadro.

## Limitações declaradas

- O universo usado aqui é a composição **de hoje** do topo do Nasdaq-100, o que
  introduz viés de sobrevivência. É aceitável para esta pergunta, que é sobre
  dispersão estrutural por nível de exposição e não sobre desempenho. O universo
  point-in-time de verdade entra no M2, arquivando a composição do QQQ a cada dia.
- O resultado depende do período: em mercado fortemente direcional a exposição pesa
  mais. Por isso o retorno do universo no período está declarado acima.
- Preço ajustado é usado aqui — e **somente aqui**, porque isto é pesquisa
  descartável e não registro publicado.

