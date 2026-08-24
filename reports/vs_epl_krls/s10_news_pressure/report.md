# Backtest de pressão textual — Diesel S10

O holdout final não foi avaliado. Os rótulos são supervisão fraca baseada no movimento posterior do preço, não anotações humanas e não evidência causal.

- Dataset de notícias: `0ad4747dfe71d570982eb0d2e242dc6ee533d4f009403977485b144baa1aff18`
- Corte de desenvolvimento: `2024-08-11`
- Limiar neutro: `R$ 0.010/L`
- Candidato apto para shadow futuro: `None`
- Melhor classificador para pesquisa de anotação: `pressure_domain_28d`
- Gate de pesquisa do classificador: `True`
- Tempo total: `200.55 s`

## Impacto na previsão

| candidate_id | mean_rmse | mean_rmse_ratio_vs_current | worst_rmse_ratio_vs_current | mean_mae | replacement_rate | eligible_for_future_shadow |
| --- | --- | --- | --- | --- | --- | --- |
| current_no_text_pressure | 0.104741 | 1.000000 | 1.000000 | 0.052381 | 0.341509 | False |
| pressure_domain_28d | 0.105018 | 1.003294 | 1.006771 | 0.052382 | 0.469484 | False |
| pressure_all_7d | 0.105094 | 1.003735 | 1.007556 | 0.052387 | 0.458491 | False |
| pressure_all_28d | 0.105030 | 1.003654 | 1.008516 | 0.052385 | 0.415094 | False |
| pressure_domain_7d | 0.105148 | 1.004400 | 1.008956 | 0.052459 | 0.330189 | False |

## Qualidade da classificação prequential

| candidate_id | accuracy | balanced_accuracy | macro_f1 | multiclass_brier | log_loss | expected_calibration_error |
| --- | --- | --- | --- | --- | --- | --- |
| pressure_domain_28d | 0.602564 | 0.522776 | 0.523043 | 0.627316 | 1.068426 | 0.220356 |
| pressure_all_7d | 0.589744 | 0.515576 | 0.521140 | 0.612957 | 1.038939 | 0.198858 |
| pressure_all_28d | 0.589744 | 0.497722 | 0.501831 | 0.650574 | 1.110866 | 0.238061 |
| pressure_domain_7d | 0.557692 | 0.472265 | 0.475984 | 0.674310 | 1.141128 | 0.267177 |

Referências: maioria do próprio período = `0.423` de acurácia; classe constante = `0.333` de acurácia balanceada. Essas referências não são modelos de produção.

## Decisão

A promoção continua proibida. Um sinal textual só pode seguir para shadow se passar o gate em todos os folds; rótulos humanos independentes e semanas futuras ainda são necessários para validação profissional.
