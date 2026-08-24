# SLOs propostos para o piloto

Estes são alvos de lançamento, não disponibilidade histórica já medida.

| SLI | SLO inicial | Medição |
|---|---:|---|
| disponibilidade da API read-only | 99,5% mensal | respostas não-5xx em `/v1/forecast` quando existe release válida |
| atualidade | 100% | `forecast_fresh=true`; previsão expirada bloqueia serving |
| integridade | 100% | release carregada somente com SHA-256 correspondente |
| latência de forecast | p95 < 100 ms | histograma externo; benchmark interno do modelo permanece < 20 ms |
| validade de saída | 100% | finita, positiva, `p10 <= point <= p90` |
| cobertura P10–P90 | 70%–95% após 26 resultados | janela prospectiva, mínimo de 20 para alerta |
| desempenho relativo | RMSE/persistência < 1,0 em 26 semanas | cálculo prospectivo, sem retuning |
| RTO | 30 minutos | exercício de rollback da release no ambiente-alvo |
| RPO | último evento oficial confirmado | ledger e release imutável replicados |

Budget de erro e escalonamento devem ser configurados no provedor escolhido. Um health 200 não substitui uma previsão atual: readiness é o sinal de tráfego.

