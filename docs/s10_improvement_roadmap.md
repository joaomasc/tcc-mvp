# Melhorias executadas e roadmap profissional — Diesel B S10

## Decisão atual

O serviço de previsão deve manter **ARIMA como primário**, persistência como fallback final e VS-ePL-KRLS como challenger. O bundle 1.1 está adequado para rollout controlado, mas o VS e o novo híbrido ainda não possuem evidência para promoção. O holdout final já foi aberto e não pode ser reutilizado para escolher a próxima versão.

> Atualização de 2026-08-24: o experimento de repasse causal ([relatório](../reports/vs_epl_krls/s10_passthrough/report.md)) fechou o espaço de busca endógeno com evidência e explica por que os challengers não passam nos gates. Leia a seção "Teto de informação" antes de abrir qualquer nova frente de modelagem.
>
> Atualização seguinte, mesma data: com dados causais novos, o **modelo de paridade de diesel superou o ARIMA no holdout** ([relatório](../reports/vs_epl_krls/s10_parity/report.md)) — RMSE 0,080807 contra 0,081463, acurácia direcional 71,8% contra 59,2% e economia R$ 19.385 contra R$ 16.962. Ele é o candidato a primário. A seção "Teto trancado por publicação" abaixo registra o ganho maior que continua fora de alcance.

## Modelo de paridade — candidato a primário

Fontes causais novas, todas automatizadas em [`21_s10_ingest_causal.py`](../scripts/21_s10_ingest_causal.py) com manifesto e SHA-256 por fonte:

| fonte | conteúdo | situação anterior |
|---|---|---|
| ULSD (`HO=F`) | futuro de diesel, USD/galão, diário | coluna 100% NaN, falha silenciosa |
| ANP produtores | preço semanal do Diesel S-10 na refinaria | ausente |
| Brent, dólar (IPEA) | diário | já existiam |

Modelo: `Δp(T) = a + b1·Δp(T−1) + b2·Δlog paridade(T−1)·p(T−1)`, Huber robusto, janela expansiva. Especificação escolhida **pela economia da política de compra**, não pelo RMSE, e congelada em código antes da leitura do holdout.

| holdout, 104 semanas | paridade | ARIMA |
|---|---:|---:|
| RMSE | **0,080807** | 0,081463 |
| acurácia direcional | **71,8%** | 59,2% |
| economia líquida | **R$ 19.385** | R$ 16.962 |
| CI90 inferior anual | **R$ 990** | R$ 117 |
| precisão do gatilho | 65,4% (26) | **75,0%** (8) |

Ressalvas registradas: a precisão do gatilho é menor (o modelo age 3× mais), 44% da economia veio de um evento, e esta foi a **segunda leitura do holdout** no projeto.

## Teto trancado por publicação

A variação semanal do preço de refinaria correlaciona **+0,566** com a variação da revenda seguinte — o sinal mais forte já medido aqui. Mas a ANP publica o arquivo ~12 dias após o fim da semana de competência, e o sinal decai com a defasagem:

| defasagem | correlação | disponível em tempo real | ganho walk-forward |
|---|---:|---|---:|
| 1 semana | +0,566 | não | **+13,7%** |
| 2 semanas | +0,224 | não | — |
| 3 semanas | +0,097 | sim | +1,7% |

**O próximo ganho material está em capturar os anúncios de reajuste da Petrobras no dia em que saem** — públicos, mas sem série baixável. É a única frente conhecida com teto alto que resta.

Defeito adicional encontrado na fonte oficial: a coluna `Brasil` do arquivo de produtores marca R$ 5,32/L em julho/2026 enquanto quatro das cinco regiões ficam em ~R$ 3,8/L, o que é impossível para média ponderada. A ingestão usa a mediana entre regiões, com teste de regressão.

## Teto de informação — resultado que muda a priorização

Três fatos medidos, não estimados:

1. **O RMSE tem tamanho amostral efetivo de ~3.** Uma única semana do holdout responde por 75,1% do erro quadrático do ARIMA; três semanas respondem por 91,2%. Os gates de 2% e o Diebold–Mariano estão sendo decididos por um punhado de pontos, e por isso nunca concluem.
2. **Em dois terços das semanas a persistência bate todos os modelos** (dev: 0,0118 contra 0,0206 do pass-through e 0,0220 do ARIMA). Modelar acrescenta ruído onde nada acontece.
3. **O teto endógeno é ~6% e já foi atingido.** Em walk-forward honesto, momentum ganha 1,8% da persistência; um oráculo que soubesse *se* haverá evento ganharia 1,5%; um oráculo que soubesse o *tamanho* do salto ganharia 90%. Todo o valor está na magnitude, que não está na série de preço.

Consequência prática: **mudar de arquitetura não produz ganho material.** Gradient boosting sobre os mesmos atributos ficou pior que regressão linear robusta e perdeu da persistência num fold. O próximo ganho exige dados causais estruturados, não mais capacidade de modelo.

## Defeitos de dados a corrigir antes de nova pesquisa

| defeito | evidência | impacto |
|---|---|---|
| `ulsd` 100% NaN | `download.py:67` recebe página de verificação de robô do stooq; `build.py:98` engole a falha | todas as colunas `ulsd_l*` são inúteis; falha silenciosa |
| `petrobras_reajuste` não é dado da Petrobras | `build.py:129` deriva do próprio preço alvo | AUC 0,19 para prever evento; documentado como atributo causal externo, não é |
| `distribuicao` termina em 2020-08-16 | `build.py:18` | perde indicador antecedente real (corr +0,277) |

## Modelo de repasse — rejeitado no holdout

Especificação de correção de erro com repasse de custo em escala econômica, estimada por Huber, congelada nos folds de desenvolvimento e avaliada uma única vez no holdout.

| | RMSE médio dev | RMSE holdout | semana parada (holdout) | economia da política |
|---|---:|---:|---:|---:|
| ARIMA | 0,105056 | **0,081463** | **0,011787** | **R$ 16.962** |
| pass-through | **0,100575** | 0,082861 | 0,021819 | R$ 7.962 |

Ganhou 4,27% no desenvolvimento, perdeu 1,7% no holdout. A causa está isolada: nas semanas de evento os dois empatam, mas nas paradas o pass-through erra quase o dobro, porque continua reagindo ao Brent quando nada é repassado. Na moeda do produto isso vira 21 gatilhos com 52,4% de precisão contra 8 gatilhos com 75%.

Hipóteses adicionais fechadas com evidência: portão de regime, zona morta sobre o ARIMA, encolhimento por limiar, alvo padronizado por volatilidade, repasse assimétrico, intervalo por mistura de regimes, escala de intervalo log-linear e intervalo condicional sobre o ARIMA — todas rejeitadas. Detalhe e números no [relatório](../reports/vs_epl_krls/s10_passthrough/report.md).

## Mudança de gates recomendada

O gate atual (ganho de 2% no RMSE, DM `p < 0,05`) não é decidível nesta série. Substituir por: MAE, métricas decompostas por regime (parada/evento), *interval score* de Winkler para incerteza, bootstrap em blocos no lugar do DM assintótico, e a economia líquida da política de compra como KPI primário.

Achado de processo a corrigir: `05_s10_model_selection.py:203` constrói apenas os conjuntos `price`, `lags` e `dynamics`. **O campeão de produção foi selecionado sem jamais ver Brent ou câmbio.**

## Melhorias concluídas

| Prioridade | Melhoria | Estado | Evidência |
|---|---|---|---|
| P0 | Escopo somente Diesel B S10 | concluída | ingestão, seleção, artefato e model card rejeitam S500/genérico |
| P0 | Avaliação temporal sem vazamento | concluída | folds expansivos, escalonamento apenas no passado e revelação atrasada do alvo |
| P0 | Holdout protegido para novos challengers | concluída | `08_s10_next_challenger.py` termina no índice 585 e grava `holdout_evaluated=false` |
| P0 | Primário/fallback seguros | concluída | ARIMA primário, persistência para saída não finita/implausível, VS em shadow |
| P0 | Artefato versionado e íntegro | concluída | contrato 1.1.0, SHA-256, fingerprint, gravação atômica e round-trip exato |
| P0 | Intervalos adaptativos | concluída | janela móvel de até 156 resíduos, atualizada somente após o observado chegar |
| P0 | Monitoramento de cobertura | concluída | cobertura e MAE online; alerta após 20 semanas se P10–P90 cobrir menos de 70% |
| P1 | Telemetria estrutural KRLS | concluída | substituições, taxa de churn, pressão de capacidade, regras e `beta` em `health()` |
| P1 | Recuperação opcional de `beta` | concluída e testada | preserva fórmula publicada quando zero; não melhorou o VS direto nos folds |
| P1 | Esquecimento e utilidade recente | concluída e testada | RLS com forgetting e `least_used` com decay; não justificou troca direta |
| P1 | Atributos externos causais | concluída em pesquisa | Brent, USD/BRL, Brent em BRL e reajuste entram apenas defasados; não venceram |
| P1 | Híbrido residual causal | concluída em shadow | aprende `real-base` somente quando o alvo chega; correção amortecida e limitada |
| P1 | Gate de estabilidade/churn | concluída | shadow exige vencer ARIMA em todos os folds e churn máximo de 40% |
| P1 | Stress e qualidade | concluída | 191 testes, stress de 1.500 amostras e cobertura `src` historicamente acima de 90% |
| P2 | CI reproduzível | concluída | workflow executa instalação, `compileall`, suíte e gate de cobertura de 90% |
| P1 | Classificador causal de pressão textual | concluída em pesquisa | 60,3% de acurácia; não melhorou RMSE e não foi promovido |
| P1 | Protocolo humano duplo e cego | preparado | lote de 300 itens; treino bloqueado até concordância e adjudicação |
| P1 | Simulação da dupla anotação | concluída e reprovada para treino | pipeline validado; classes direcionais insuficientes mesmo após calibração |

## Resultado das hipóteses

- VS direto: o candidato atual permaneceu primeiro. Recuperação de `beta`, forgetting, dicionário 30/40 e exógenas não produziram ganho robusto.
- Melhor média híbrida: `hybrid_lags_paper`, razão média de RMSE 0,9427 contra ARIMA, mas razão 1,0729 no pior fold. Rejeitado por instabilidade.
- Shadow estável: `hybrid_dynamics_conservative`, razão média 0,9946 e pior razão 0,9981, latência interna p95 2,23 ms, 20 regras e churn 34,4%.
- Conclusão: a correção conservadora é tecnicamente interessante, mas o ganho médio de aproximadamente 0,54% é pequeno e ainda não é evidência de produção.

## Próximas etapas que dependem de dados futuros ou plataforma

1. **Em andamento — 1/26:** acumular no mínimo 26 semanas futuras sem ajustar o challenger; 52 semanas são preferíveis. A realização oficial de 2026-08-16 foi registrada com proveniência ANP; faltam 25 semanas para o gate mínimo.
2. Registrar, para ARIMA e híbrido congelado, previsão, intervalo, latência e erro antes de cada atualização.
3. Reavaliar RMSE/MAE/SMAPE, pior janela de 13 semanas, cobertura e Diebold–Mariano no período realmente novo.
4. Promover somente se o ganho prático superar o gate acordado, não houver regressão relevante em subperíodos e churn/latência permanecerem dentro do orçamento.
5. Integrar métricas do JSON de saúde ao sistema real de observabilidade e alertas. O repositório fornece os sinais, mas não escolhe a plataforma externa.
6. Fazer revisão independente da correspondência matemática com o código original dos autores, caso ele se torne disponível.
7. Concluir duas anotações independentes do lote S10, exigir kappa mínimo de 0,60 e adjudicar divergências antes de treinar um classificador supervisionado humano.

## Freeze prospectivo ativo

- Candidato: `hybrid_dynamics_conservative`.
- Fingerprint: `7410bb7e767e1e565bd87730fea945be432a46595948e39952211c5c08cfd6a7`.
- Artefato inicial: `artifacts/s10_shadow_hybrid_v1.joblib`.
- SHA-256 inicial: `e7beb82a923b20cdc85a3bb65e5f984b92299c22485009826aef2f23011cac6e`.
- Ledger: `reports/vs_epl_krls/s10_shadow/shadow_ledger.jsonl`.
- Head inicial do ledger: `41240d26ffac6967be33da08510304593eede1a3923b9b8ffeba4abb150f6d8a`.
- Forecast pendente: R$ 6,8824347/L para 2026-08-23.
- Estado: 1 resultado, 25 restantes para análise mínima, promoção automática proibida.

O candidato congelado ocupa 20/20 regras e 20/20 elementos no maior dicionário após o refit completo; isso é um warning prospectivo relevante. Alterar capacidade agora criaria outro candidato e invalidaria o freeze atual.

## Critérios de saída para promoção do challenger

- nenhum ajuste usando o holdout de 104 semanas já observado;
- período futuro congelado e rastreável;
- previsões 100% finitas e sem vazamento;
- desempenho consistente contra ARIMA e persistência;
- cobertura P10–P90 operacional entre 70% e 95%;
- p95 end-to-end abaixo de 20 ms no ambiente-alvo;
- regras e dicionários dentro dos limites, sem churn sustentado acima de 40%;
- aprovação humana do lineage dos dados, incidentes e relatório estatístico.
