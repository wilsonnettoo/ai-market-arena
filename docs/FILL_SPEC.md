# FILL_SPEC v1.0.0

**Datado em 2026-07-30. Implementado no marco M4.** Congelado: mudança exige bump de versão,
entrada em `docs/DECISOES.md` e nova temporada.

O valor deste documento está em ser **datado antes de o simulador existir**. Preenchimento é
função pura de `(ordem, barras posteriores)`. Como toda barra é arquivada com o horário de
ingestão, a carteira pode ser reconstruída por qualquer terceiro a partir destas regras — e é
por isso que o Ledger não custa tempo de calendário.

---

## Ciclo de vida da ordem

```
proposta -> publicada -> ativa -> {parcial -> preenchida | preenchida | stopada | expirada} -> encerrada
```

Ordem que nunca preenche termina em `expirada` e **permanece no histórico**. A taxa de
não-preenchimento é métrica de capa do painel.

Ordem que evapora do registro é o mecanismo número um de inflação de track record no mundo
inteiro: publica-se a intenção, ela não executa, e o histórico só mostra as que deram certo.

---

## Regras

1. **LIMIT de compra.** Preenche no pregão seguinte à publicação se `low <= entry_limit`.
   Preço de execução = `min(open, entry_limit)`. Validade: 2 pregões; depois, `expirada`.

2. **Gap de abertura.** Se `open <= entry_limit`, executa em `open`, **nunca** em
   `entry_limit`. Supor execução no limite quando o mercado abriu melhor é inventar lucro
   que não existiu.

3. **STOP.** Ordem repousando, avaliada contra o OHLC de cada pregão. Se `low <= stop`,
   executa em `min(open, stop)`. Em gap de abertura abaixo do stop, executa em `open`.

4. **TARGET.** Se `high >= target`, executa em `max(open, target)`.

5. **Stop e target no mesmo pregão.** Assume-se o **pior caso: stop primeiro.** Barra diária
   não permite ordenar os dois eventos, e supor o melhor caso é a forma mais comum de inflar
   backtest.

6. **Preenchimento parcial.** Se o tamanho da ordem exceder 1% do volume do pregão, preenche
   apenas 1% do volume; o restante segue `ativa` até expirar.

7. **Custos.** Comissão zero (corretora americana de varejo). Slippage de 1 ponto-base
   aplicado **contra** a posição em toda execução. Spread já está embutido na regra de gap.

8. **Ações corporativas.** Split ajusta quantidade e todos os preços da ordem pelo fator, na
   data efetiva. Dividendo credita caixa. **Nenhum preço ajustado é gravado:** o cálculo parte
   sempre do bruto mais a tabela de ações corporativas.

9. **Deslistagem ou saída do índice.** Posição encerrada no último fechamento disponível;
   ordens ativas viram `expirada`. A previsão associada vira `void`.

10. **Isolamento entre personas.** Cada persona é instância separada de
    (Ledger, Simulador, Gestor de Risco) sobre um snapshot de mercado somente-leitura. Não há
    estado escrito compartilhado, e o simulador não modela impacto agregado entre carteiras.
    Os limites de perda diária e semanal são **por carteira**, nunca globais — senão o
    guardião paga pelo erro do agressivo.

---

## O que este documento deliberadamente não modela

Impacto de mercado da própria ordem, fila de execução, latência, execução intradiária, e
liquidez em profundidade de book. Todos exigiriam dados que o projeto não compra
(`docs/DECISOES.md` D2) e nenhum é relevante para ordens de no máximo US$ 8.000 em megacaps
do Nasdaq-100, onde o spread é da ordem de um ponto-base.

Declarar a limitação é parte da regra: o resultado publicado é ajustado por estas premissas e
não pretende ser execução real.
