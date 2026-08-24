# S10 next challenger — relatório de desenvolvimento

Este experimento não reabriu o holdout final e não autoriza promoção.

- Candidatos VS diretos: 13
- Candidatos híbridos: 9
- Tempo: 117.86 s
- Melhor VS direto: `current_vs_baseline`
- Melhor híbrido: `hybrid_dynamics_conservative`
- Melhor média híbrida (pode ser instável): `hybrid_lags_paper`

## Comparação média nos folds de desenvolvimento

| model | mean_rmse | worst_rmse | mean_mae | mean_smape |
| --- | --- | --- | --- | --- |
| ARIMA+VS residual | 0.104560 | 0.165121 | 0.052552 | 0.853556 |
| ARIMA | 0.105057 | 0.165455 | 0.052735 | 0.857217 |
| VS atual | 0.108159 | 0.166146 | 0.057490 | 0.944430 |
| VS next | 0.108159 | 0.166146 | 0.057490 | 0.944430 |
| persistência | 0.114094 | 0.167514 | 0.055949 | 0.921142 |

## Decisão

O candidato elegível fica em shadow research. Para ser elegível, precisa superar ARIMA em todos os folds e manter churn de substituição em até 40%. Somente dados futuros ainda não observados podem liberar promoção.