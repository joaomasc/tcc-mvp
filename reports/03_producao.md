# Bloco 3 — Modelo final de producao

**Recomendado (h=1 semana, criterio RMSE walk-forward): ARIMA**

Modelo recomendado para producao com base no RMSE walk-forward de 1 semana. Se VS-ePL-KRLS nao for o vencedor, ele permanece como candidato evolutivo porque atualiza a cada observacao e fornece sinais de drift via beta e regras.

## Ranking h=1

| model | rmse | mae | smape | dir_acc | coverage_p10_p90 |
| --- | --- | --- | --- | --- | --- |
| ARIMA | 0.07262 | 0.02789 | 0.56698 | 0.63636 | 0.66044 |
| ARIMAX | 0.07490 | 0.02937 | 0.59253 | 0.63451 | 0.64346 |
| naive | 0.07861 | 0.03069 | 0.62560 | 0.00000 | 0.64346 |
| media_movel | 0.13887 | 0.06740 | 1.36501 | 0.29499 | 0.62479 |
| XGBoost | 0.24026 | 0.13675 | 2.79832 | 0.41002 | 0.63497 |
| LightGBM | 0.24790 | 0.14219 | 2.97182 | 0.39889 | 0.63497 |
| VS-ePL-KRLS | 3.41421 | 3.24282 | 130.07866 | 0.50464 | 0.45840 |
| LSTM | 4.08798 | 3.82918 | 138.90568 | 0.50464 | 0.54329 |

## Previsao da proxima semana (preco medio nacional de revenda, R$/L)

- Semana observada: 2026-08-09
- Preco observado: 6.91
- Previsao pontual: 6.89807791495677
- P10: 6.864345518329333
- P90: 6.918269486734574
- Prob. alta / estavel / queda: {'p_alta': 0.075, 'p_estavel': 0.4625, 'p_queda': 0.4625}

## Model card

- Alvo: preco medio nacional de *revenda* do Diesel B S-10 (ANP), nao o preco de um posto.
- Horizonte de producao: 1 semana a frente.
- Frequencia de atualizacao: incremental a cada nova semana da ANP.
- Exogenas: Brent, USD/BRL, diesel internacional (se disponivel), defasagens, medias moveis, volatilidade, proxy de reajuste Petrobras.
- Preco de distribuicao: usado so na reproducao do artigo; serie ANP termina em ago/2020.
- Intervalo P10-P90: quantis conformais dos residuos walk-forward, nao intervalos gaussianos.
- Limitacoes: buraco ANP ago-out/2020; mudancas de politica de precos; o modelo nao antecipa reajuste da Petrobras no mesmo dia em que e anunciado se a semana ainda nao fechou.
- Quando reajustar: alerta Page-Hinkley, PSI alto nas exogenas, ou degradacao do RMSE movel de 12 semanas.

Este bloco nao declara reproducao do artigo. A reproducao esta no relatorio 01.