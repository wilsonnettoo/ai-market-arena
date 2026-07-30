# Manifesto — AI Market Arena

Documento de pré-registro. Escrito e carimbado **antes** de existir a primeira previsão.
Correções são feitas por acréscimo, nunca por edição.

## A pergunta

Três políticas de decisão com filosofias de risco declaradamente diferentes, operando
capital fictício sobre o mesmo universo (Nasdaq-100), produzem previsões mensuravelmente
melhores que o azar e que baselines triviais?

## A métrica-manchete

Brier Skill Score contra climatologia, com intervalo de confiança por bootstrap. Baselines
obrigatórios publicados ao lado, sempre: climatologia, moeda justa (0,50), otimista fixo
(0,55) e momentum 12-1.

Toda métrica publicada sai com intervalo de confiança e com o número de observações. Para
distinguir 60% de acerto de uma moeda são necessárias cerca de 194 observações; nenhuma
alegação será feita com amostra menor que a exigida pela alegação.

## Como o fracasso é declarado

O desfecho mais provável é **habilidade não mensurável** — Brier Skill Score próximo de zero
com intervalo de confiança cruzando zero. **Esse resultado será publicado com o mesmo
destaque de um resultado positivo.**

Nenhuma regra, prompt, limite ou coeficiente é alterado para melhorar um número já
publicado. A regra de previsão e seus coeficientes estão congelados em
`policy/forecast_rule.yaml`, definidos a priori e sem ajuste a dados históricos.

## O que este projeto não afirma

Que a inteligência artificial prevê o futuro. Que existe taxa de acerto garantida. Que o
sistema supera o Nasdaq. Que alguém deve copiar qualquer operação. Que resultado passado se
repete. Que paper trading representa o mercado real.

## Regras de integridade

1. Todo registro é publicado antes do resultado.
2. `entry_limit`, `stop` e `target` são publicados sob hash em T0 e revelados no fechamento
   do horizonte. Todo o resto vai em claro em T0.
3. Nenhum registro publicado é editado. Correção é registro novo.
4. Cada dia de pregão gera exatamente uma entrada na cadeia. Dia sem previsão gera
   `OutageRecord` — silêncio nunca.
5. A regra de previsão e seus coeficientes são congelados antes da primeira previsão e
   versionados.
6. Nenhuma chamada de modelo de linguagem participa das previsões publicadas antes do marco
   M7, e a data dessa transição é anunciada e carimbada antes de acontecer.
7. Toda resposta de API é arquivada de forma imutável, com o horário de ingestão, antes de
   ser interpretada.

## Como auditar

```bash
uv run python scripts/verify_chain.py
```

O verificador recomputa a cadeia inteira a partir do registro gênese e confere o hash de
cada arquivo publicado contra os bytes em disco. `chain/CHAIN.jsonl.ots` é a atestação
OpenTimestamps, ancorada no Bitcoin: ela prova que o conteúdo existia antes do bloco que a
contém.

O `main` deste repositório tem proteção de histórico com force-push desabilitado inclusive
para administradores. Isso importa porque, sem ele, a data de autoria de um commit é um campo
que o autor escolhe — e "commit público no GitHub" não provaria anterioridade a ninguém.

## Capital

Fictício. Sempre. Nenhuma credencial de conta real está acessível ao sistema.

## Conflito de interesse

As posições pessoais do autor em ativos do Nasdaq-100 e no QQQ serão declaradas em página
fixa do painel. A forma dessa declaração está pendente de decisão registrada
(`docs/DECISOES.md`, D14) e será publicada antes do primeiro vídeo.

---

**Este não é serviço de recomendação de investimento.** É um experimento educacional e de
pesquisa, com capital fictício, cujo objeto de estudo é a própria calibração das previsões.
