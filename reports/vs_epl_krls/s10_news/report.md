# Backtest de notícias — Diesel S10

O holdout final não foi reaberto. Este relatório não autoriza promoção.

- Dataset semanal v3: `523a8d502025fc72ea6b87154f114eeeb22735fd2580645f3a4ad562b3c120c9`
- Folds: 3 x 52 semanas (156 previsões)
- Candidato selecionado para shadow futuro: `None`
- Tempo: 73.26 s

## Ranking

| candidate_id | mean_rmse | worst_rmse | mean_mae | mean_smape | mean_rmse_ratio_vs_current | worst_rmse_ratio_vs_current | mean_rmse_ratio_vs_arima | worst_rmse_ratio_vs_arima | replacement_rate | max_rules | max_dictionary_size | latency_ms_p95 | beats_current_all_folds | beats_arima_all_folds | bounded_replacement_churn | eligible_for_future_shadow | selection_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_no_news | 0.104741 | 0.165091 | 0.052381 | 0.850523 | 1.000000 | 1.000000 | 0.994996 | 0.998008 | 0.341509 | 20 | 20 | 2.590485 | False | True | True | False | 1.200000 |
| news_impact_sigma015 | 0.104926 | 0.165188 | 0.052278 | 0.849137 | 1.002116 | 1.004547 | 0.997094 | 0.999151 | 0.345070 | 20 | 20 | 3.124350 | False | True | True | False | 1.203238 |
| news_core_sigma015 | 0.104953 | 0.165255 | 0.052210 | 0.847959 | 1.002273 | 1.005135 | 0.997249 | 0.999000 | 0.471698 | 20 | 20 | 3.009150 | False | True | False | False | 1.203548 |
| news_all_sigma030 | 0.104902 | 0.164961 | 0.052320 | 0.850149 | 1.002134 | 1.008104 | 0.997102 | 0.997218 | 0.477358 | 20 | 20 | 3.138705 | False | True | False | False | 1.204272 |
| news_core_sigma030 | 0.104984 | 0.164925 | 0.052523 | 0.852344 | 1.003178 | 1.011583 | 0.998133 | 1.000498 | 0.381132 | 20 | 20 | 3.096920 | False | False | True | False | 1.206222 |

## Qualidade do sinal nos folds

```json
{
  "validation_origins": 156,
  "origins_with_news": 94,
  "no_news_rate": 0.3974358974358974,
  "mean_source_coverage": 0.2724358974358974,
  "mean_article_count_log1p": 2.099729022010889
}
```

## Decisão

Somente um candidato que passe o gate em todos os folds pode seguir para shadow prospectivo. Mesmo assim, dados futuros ainda não observados são obrigatórios antes de qualquer uso operacional.
