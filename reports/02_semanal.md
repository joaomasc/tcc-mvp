# Bloco 2 — Adaptacao semanal

Validacao walk-forward temporal (sem divisao aleatoria).
VS-ePL-KRLS atualiza de forma incremental. Modelos em lote reajustam a cada 4 semanas (LSTM a cada 8).
Features apenas defasadas. Preco de distribuicao NAO entra no modelo de producao apos ago/2020.

## Resultados

| horizon | model | rmse | mae | smape | dir_acc | coverage_p10_p90 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | VS-ePL-KRLS | 3.41421 | 3.24282 | 130.079 | 0.50464 | 0.45840 |
| 1 | naive | 0.07861 | 0.03069 | 0.62560 | 0.00000 | 0.64346 |
| 1 | media_movel | 0.13887 | 0.06740 | 1.36501 | 0.29499 | 0.62479 |
| 1 | ARIMA | 0.07262 | 0.02789 | 0.56698 | 0.63636 | 0.66044 |
| 1 | ARIMAX | 0.07490 | 0.02937 | 0.59253 | 0.63451 | 0.64346 |
| 1 | LightGBM | 0.24790 | 0.14219 | 2.97182 | 0.39889 | 0.63497 |
| 1 | XGBoost | 0.24026 | 0.13675 | 2.79832 | 0.41002 | 0.63497 |
| 1 | LSTM | 4.08798 | 3.82918 | 138.906 | 0.50464 | 0.54329 |
| 2 | VS-ePL-KRLS | 3.38837 | 3.20895 | 128.508 | 0.47213 | 0.45408 |
| 2 | naive | 0.13158 | 0.05760 | 1.16590 | 0.00000 | 0.64116 |
| 2 | media_movel | 0.18006 | 0.09196 | 1.86442 | 0.29965 | 0.61735 |
| 2 | ARIMA | 0.12487 | 0.05375 | 1.08353 | 0.61672 | 0.64116 |
| 2 | ARIMAX | 0.12804 | 0.05571 | 1.11694 | 0.63240 | 0.61905 |
| 2 | LightGBM | 0.28769 | 0.17475 | 3.62308 | 0.37631 | 0.62925 |
| 2 | XGBoost | 0.28431 | 0.17252 | 3.54838 | 0.40418 | 0.63605 |
| 2 | LSTM | 4.09071 | 3.83246 | 138.956 | 0.47213 | 0.54422 |
| 4 | VS-ePL-KRLS | 3.40450 | 3.22983 | 129.575 | 0.45034 | 0.43686 |
| 4 | naive | 0.21070 | 0.10690 | 2.16481 | 0.00000 | 0.61945 |
| 4 | media_movel | 0.24712 | 0.13803 | 2.80133 | 0.29452 | 0.59215 |
| 4 | ARIMA | 0.20531 | 0.10258 | 2.06716 | 0.61986 | 0.63311 |
| 4 | ARIMAX | 0.21013 | 0.10607 | 2.12692 | 0.64041 | 0.63311 |
| 4 | LightGBM | 0.35910 | 0.23108 | 4.83014 | 0.41267 | 0.58703 |
| 4 | XGBoost | 0.35764 | 0.23111 | 4.73955 | 0.39212 | 0.61433 |
| 4 | LSTM | 4.09623 | 3.83910 | 139.056 | 0.45034 | 0.56826 |

## Melhor por horizonte (RMSE)

| horizon | model | rmse | mae | smape | dir_acc |
| --- | --- | --- | --- | --- | --- |
| 1 | ARIMA | 0.07262 | 0.02789 | 0.56698 | 0.63636 |
| 2 | ARIMA | 0.12487 | 0.05375 | 1.08353 | 0.61672 |
| 4 | ARIMA | 0.20531 | 0.10258 | 2.06716 | 0.61986 |

## Previsao 1 semana a frente (ultimo ponto da amostra)

```json
{
  "modelo": "ARIMA",
  "ultima_semana_observada": "2026-08-09",
  "preco_observado_ultima_semana": 6.91,
  "horizonte": "1 semana",
  "previsao_pontual": 6.89807791495677,
  "p10": 6.864345518329333,
  "p90": 6.918269486734574,
  "probabilidades": {
    "p_alta": 0.075,
    "p_estavel": 0.4625,
    "p_queda": 0.4625
  },
  "aviso": "Previsao do preco medio nacional de REVENDA. Nao e preco de bomba de um posto especifico."
}
```

Os numeros do bloco 1 (artigo mensal 2012-2020) nao se transferem para este bloco.