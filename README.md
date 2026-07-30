# AI Market Arena

Registro público e auditável de previsões de mercado sobre o Nasdaq-100, **publicadas antes do
resultado**. Capital fictício.

> **Temporada Zero — sistema em validação.**
> Experimento educacional e de pesquisa. **Não é recomendação de investimento.**

Leia o [Manifesto](./MANIFESTO.md): a pergunta, a métrica-manchete e como o fracasso será
declarado — escritos e carimbados antes de a primeira previsão existir.

## Verifique você mesmo

```bash
uv sync
uv run python scripts/verify_chain.py
```

O verificador recomputa a cadeia de hash a partir do registro gênese e confere o hash de cada
arquivo publicado contra os bytes em disco. Não é necessário confiar em mim para conferir isso.

`chain/CHAIN.jsonl.ots` é a atestação [OpenTimestamps](https://opentimestamps.org): ela prova,
via Bitcoin, que o conteúdo existia antes do bloco que o ancora.

O `main` deste repositório tem histórico linear e force-push desabilitado inclusive para
administradores — sem isso, a data de autoria de um commit seria apenas um campo que o autor
escolhe.

## Por que isto existe

A tese não é que a inteligência artificial preveja o mercado. É que decisões registradas antes
do resultado, com metodologia congelada e erros reconhecidos publicamente, são raras — e
verificáveis. O placar é o enredo; o registro é o produto.

## Estrutura

| Caminho | O que é |
|---|---|
| `arena/canonical.py` | Forma canônica de serialização e hash. Normativo. |
| `arena/contracts/` | Contratos congelados, versão 1.0.0 |
| `arena/audit/` | Cadeia de hash append-only e publicador |
| `policy/` | Regra de previsão e limites de risco, congelados e versionados |
| `docs/MANIFESTO.md` … | Pré-registro, especificação de execução, decisões |
| `docs/ESTADO.md` | Onde o projeto está e o que falta |
| `chain/CHAIN.jsonl` | A cadeia. Uma linha por dia de pregão. |
| `data/` | Registros publicados. Append-only. |

## Licença

Código sob MIT. Dados publicados (previsões, resultados, métricas) sob CC-BY 4.0. Séries de
cotação **não** são redistribuídas — apenas o preço de referência usado em cada decisão e os
retornos derivados dele.
