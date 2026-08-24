# Revisao por gates decidiveis — Diesel B S10

Repontuacao das previsoes ja publicadas com metricas que concluem. Nao houve
treino, selecao nem nova leitura do holdout: as especificacoes ja estavam
congeladas, e o que muda aqui e a regua.

Janela: 2024-08-18 a 2026-08-09, 104 semanas.

## Resumo

1. O modelo de paridade decide melhor do que preve: passa nos gates economicos (economia_anual_ci90_positiva, economia_supera_incumbente, economia_nao_concentrada) e falha em mae_melhor_que_incumbente, sem_regressao_em_semana_parada.
2. O VS-ePL-KRLS nao passa: falha em economia_anual_ci90_positiva, economia_supera_incumbente, economia_nao_concentrada, mae_melhor_que_incumbente, sem_regressao_em_semana_de_evento, sem_regressao_em_semana_parada.
3. O intervalo publicado cobre 89.4% para um nominal de 80%; a recalibracao conformal chega a 80.8% com banda 28.3% mais estreita e Winkler melhor.

O gate antigo — 2% de RMSE mais Diebold-Mariano normal — nao decidia nenhuma das
tres perguntas. Todas as tres tem resposta agora, e as respostas nao sao as que o
RMSE sugeria.

## Acuracia por modelo, decomposta por regime

| modelo | mae | mae_quiet | mae_event | rmse | largest_error_share_of_sse |
|---|---|---|---|---|---|
| paridade | 0.027521 | 0.011439 | 0.059226 | 0.080807 | 0.760200 |
| ARIMA | 0.027069 | 0.007946 | 0.064768 | 0.081463 | 0.750941 |
| persistencia | 0.032596 | 0.005942 | 0.085143 | 0.095630 | 0.575754 |

A ultima coluna e a razao de tudo isto existir: a fracao do erro quadratico total
que vem de um unico ponto. Enquanto ela estiver nessa ordem de grandeza, qualquer
conclusao apoiada em RMSE esta sendo decidida por uma semana.

## 1. Paridade contra ARIMA

| name | passed | observed | threshold |
|---|---|---|---|
| economia_anual_ci90_positiva | sim | 923.076923 | 0.000000 |
| economia_supera_incumbente | sim | 2,423 | 0.000000 |
| economia_nao_concentrada | sim | 0.440476 | 0.600000 |
| mae_melhor_que_incumbente | **nao** | 0.002178 | 0.000000 |
| sem_regressao_em_semana_de_evento | sim | -0.085570 | 0.050000 |
| sem_regressao_em_semana_parada | **nao** | 0.439541 | 0.050000 |
| intervalo_calibrado | sim | 0.094231 | 0.100000 |

Veredito: **nao promover**. O modelo de paridade decide melhor do que preve: passa nos gates economicos (economia_anual_ci90_positiva, economia_supera_incumbente, economia_nao_concentrada) e falha em mae_melhor_que_incumbente, sem_regressao_em_semana_parada.

## 2. VS-ePL-KRLS contra ARIMA

| name | passed | observed | threshold |
|---|---|---|---|
| economia_anual_ci90_positiva | **nao** | -0.000000 | 0.000000 |
| economia_supera_incumbente | **nao** | -13,962 | 0.000000 |
| economia_nao_concentrada | **nao** | 0.846154 | 0.600000 |
| mae_melhor_que_incumbente | **nao** | 0.012428 | 0.000000 |
| sem_regressao_em_semana_de_evento | **nao** | 0.258967 | 0.050000 |
| sem_regressao_em_semana_parada | **nao** | 0.168537 | 0.050000 |

Veredito: **nao promover**. O VS-ePL-KRLS nao passa: falha em economia_anual_ci90_positiva, economia_supera_incumbente, economia_nao_concentrada, mae_melhor_que_incumbente, sem_regressao_em_semana_de_evento, sem_regressao_em_semana_parada.

## 3. Intervalo publicado contra recalibracao conformal

| intervalo | empirical_coverage | calibration_error | mean_width | mean_winkler |
|---|---|---|---|---|
| publicado | 0.894231 | 0.094231 | 0.083330 | 0.182073 |
| conformal adaptativo | 0.807692 | 0.007692 | 0.059771 | 0.178687 |

Cobertura acima do nominal nao e seguranca gratuita: a banda larga desloca o
cenario P90 e distorce o custo aparente da decisao. O conformal adaptativo chega
perto do nominal com banda mais estreita **e** Winkler melhor, ou seja, nao esta
trocando cobertura por largura — esta corrigindo um nivel que estava errado.

