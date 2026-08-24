# Protocolo de anotação — pressão de notícias sobre Diesel S10

## Objetivo e estado

O lote `s10-news-annotation.v1` serve para criar rótulos humanos independentes de **pressão esperada sobre o preço nacional semanal de revenda do Diesel B S10**. Ele não mede sentimento genérico e não deve ser confundido com causalidade comprovada.

O manifesto começa com `training_allowed=false`. Nenhum rótulo pode alimentar treino ou seleção enquanto as duas anotações, a validação, a concordância e a adjudicação não estiverem concluídas.

## Procedimento cego

Cada item é enviado a dois anotadores em arquivos separados. A fila humana não contém direção, relevância ou intensidade calculada pelo léxico, nem revela quais itens pertencem ao grupo de controle.

O anotador deve:

1. usar somente título, resumo, fonte, URL e informação pública disponível até `first_available_at`;
2. não consultar movimentos posteriores do preço do S10;
3. não conversar com o outro anotador antes do fechamento independente;
4. preencher seu identificador e `annotated_at_utc` em ISO 8601, por exemplo `2026-08-23T15:00:00Z`;
5. registrar evidência curta e um racional próprio;
6. não editar identificadores, texto-fonte, URL, datas ou `annotation_slot`.

## Código dos rótulos

`relevance_label`:

- `0`: sem relação plausível com custo, oferta ou demanda de S10;
- `1`: relação indireta, localizada ou fraca;
- `2`: relação material, porém sem mecanismo nacional imediato explícito;
- `3`: mecanismo direto e material para preço, oferta, tributação, mistura, refino ou logística do S10.

`direction_label`:

- `down`: tende a reduzir preço/custo ou ampliar oferta líquida;
- `neutral`: relevante, mas sem pressão direcional material;
- `up`: tende a elevar preço/custo ou reduzir oferta líquida;
- `uncertain`: mecanismos conflitantes ou informação insuficiente.

`intensity_label`:

- `0`: nenhuma pressão material;
- `1`: fraca ou localizada;
- `2`: moderada e potencialmente nacional;
- `3`: forte, direta e potencialmente imediata.

`horizon_label`:

- `1w`, `2w` ou `4w`: janela principal esperada;
- `long`: efeito esperado depois de quatro semanas;
- `unknown`: não há base suficiente para escolher uma janela.

O limiar de R$ 0,01/L usado na supervisão fraca do benchmark não deve ser mostrado ao anotador como movimento realizado. Para uma empresa que compra 200 mil litros/mês, esse valor corresponde a R$ 2 mil e funciona apenas como referência de materialidade do projeto.

## Geração, merge e validação

```bash
python scripts/12_prepare_news_annotations.py \
  --news-records CAMINHO/news-record/v2

# Depois que cada profissional preencher apenas seu arquivo:
python scripts/12_prepare_news_annotations.py \
  --merge-completed data/annotations/s10_news_pressure_v1.annotator_1.csv \
                    data/annotations/s10_news_pressure_v1.annotator_2.csv
```

O merge rejeita alterações no conteúdo imutável, duplicidade de slot, o mesmo anotador nos dois slots, rótulos inválidos, timestamps ausentes e campos obrigatórios em branco. Ele calcula Cohen's kappa para relevância, direção, intensidade e horizonte.

## Gate de concordância e adjudicação

- Meta inicial: `kappa >= 0,60` em relevância e direção.
- Abaixo de `0,60`: revisar o guia, fazer calibração dos anotadores e repetir uma amostra; não treinar.
- Divergências remanescentes devem ser decididas por um terceiro especialista, sem apagar os dois rótulos originais.
- O conjunto de treino final deve guardar rótulos originais, decisão adjudicada, versão do guia, IDs dos anotadores e hashes dos arquivos.

O pipeline atual valida e calcula concordância; a adjudicação permanece uma decisão humana intencional.

## Simulação executada

Para testar o processo antes de envolver pessoas, `13_simulate_news_annotations.py` executa duas políticas separadas: análise de oferta/custos e análise conservadora de risco de compras. Nenhuma delas consulta preços futuros. Os resultados são gravados fora dos arquivos humanos e carregam `human_annotations=false`, `production_training_allowed=false` e `model_promotion_allowed=false`.

```bash
python scripts/13_simulate_news_annotations.py
```

Na primeira rodada, relevância obteve κ=0,578 e direção κ=0,507; 92 de 300 itens divergiram e o gate de concordância reprovou. Depois de calibrar a definição de relação indireta, relevância chegou a κ=0,912 e restaram 18 divergências. Mesmo assim, o gate final continuou reprovado: as políticas produziram zero rótulos `down`, apenas um `up` e nenhum caso de intensidade 2 ou 3. Concordância alta com classes degeneradas não forma um conjunto útil para direção.

Os relatórios ficam em `reports/vs_epl_krls/s10_news_annotation_simulation/` e `reports/vs_epl_krls/s10_news_annotation_simulation_calibrated/`. A simulação comprova o funcionamento técnico do fluxo, mas também mostra por que julgamento humano sobre mecanismo econômico ainda é necessário.
