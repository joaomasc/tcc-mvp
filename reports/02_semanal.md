# Bloco 2 — Adaptacao semanal

Validacao walk-forward temporal (sem divisao aleatoria).
VS-ePL-KRLS atualiza de forma incremental. Modelos em lote reajustam a cada 4 semanas (LSTM a cada 8).
Features apenas defasadas. Preco de distribuicao NAO entra no modelo de producao apos ago/2020.

## Resultados

| horizon | model | rmse | mae | smape | dir_acc | coverage_p10_p90 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | VS-ePL-KRLS | 3.41660 | 3.24599 | 130.258 | 0.50372 | 0.17687 |
| 1 | naive | 0.07867 | 0.03069 | 0.62591 | 0.00000 | 0.00340 |
| 1 | media_movel | 0.13898 | 0.06746 | 1.36643 | 0.29554 | 0.01701 |
| 1 | ARIMA | 0.07267 | 0.02789 | 0.56730 | 0.63569 | 0.00170 |
| 1 | ARIMAX | 0.07484 | 0.02928 | 0.59115 | 0.63383 | 0.00340 |
| 1 | LightGBM | 0.24780 | 0.14193 | 2.96967 | 0.39963 | 0.07653 |
| 1 | XGBoost | 0.23869 | 0.13484 | 2.75870 | 0.40892 | 0.07823 |
| 1 | LSTM | 4.08382 | 3.82542 | 138.873 | 0.50372 | 0.18197 |
| 2 | VS-ePL-KRLS | 3.39033 | 3.21121 | 128.669 | 0.47120 | 0.18739 |
| 2 | naive | 0.13168 | 0.05763 | 1.16687 | 0.00000 | 0.01022 |
| 2 | media_movel | 0.18020 | 0.09204 | 1.86648 | 0.30017 | 0.03578 |
| 2 | ARIMA | 0.12496 | 0.05378 | 1.08437 | 0.61780 | 0.00681 |
| 2 | ARIMAX | 0.12785 | 0.05552 | 1.11396 | 0.63176 | 0.00681 |
| 2 | LightGBM | 0.28791 | 0.17493 | 3.62748 | 0.37696 | 0.07836 |
| 2 | XGBoost | 0.28205 | 0.17015 | 3.50643 | 0.40663 | 0.09710 |
| 2 | LSTM | 4.08655 | 3.82870 | 138.923 | 0.47120 | 0.18228 |
| 4 | VS-ePL-KRLS | 3.40634 | 3.23186 | 129.733 | 0.44940 | 0.18974 |
| 4 | naive | 0.21087 | 0.10702 | 2.16767 | 0.00000 | 0.04444 |
| 4 | media_movel | 0.24730 | 0.13812 | 2.80394 | 0.29503 | 0.07350 |
| 4 | ARIMA | 0.20548 | 0.10273 | 2.07032 | 0.61921 | 0.03932 |
| 4 | ARIMAX | 0.20945 | 0.10548 | 2.11708 | 0.63979 | 0.03419 |
| 4 | LightGBM | 0.35928 | 0.23108 | 4.83257 | 0.41166 | 0.10256 |
| 4 | XGBoost | 0.35874 | 0.22912 | 4.72774 | 0.39280 | 0.08718 |
| 4 | LSTM | 4.09207 | 3.83534 | 139.024 | 0.44940 | 0.17949 |

## Melhor por horizonte (RMSE)

| horizon | model | rmse | mae | smape | dir_acc |
| --- | --- | --- | --- | --- | --- |
| 1 | ARIMA | 0.07267 | 0.02789 | 0.56730 | 0.63569 |
| 2 | ARIMA | 0.12496 | 0.05378 | 1.08437 | 0.61780 |
| 4 | ARIMA | 0.20548 | 0.10273 | 2.07032 | 0.61921 |

## Previsao 1 semana a frente (ultimo ponto da amostra)

```json
{
  "ultima_semana_observada": "2026-08-02",
  "preco_observado_ultima_semana": 6.94,
  "horizonte": "1 semana",
  "previsao_pontual": 5.569556804802472,
  "p10": 7.4324292859346945,
  "p90": 10.575437512922795,
  "probabilidades": {
    "p_alta": 1.0,
    "p_estavel": 0.0,
    "p_queda": 0.0
  },
  "n_regras": 1,
  "aviso": "Previsao do preco medio nacional de REVENDA. Nao e preco de bomba de um posto especifico."
}
```

Os numeros do bloco 1 (artigo mensal 2012-2020) nao se transferem para este bloco.