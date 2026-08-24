# Modelo de paridade de diesel — dados causais, ingestão automatizada e resultado

Data: 2026-08-24. Escopo: previsão de uma semana do preço médio nacional de
revenda do Diesel B S10, com decisão de antecipação de compra.

**Resultado: o modelo de paridade supera o ARIMA no holdout em acurácia, direção
e economia. Ele é o candidato a primário.** Este relatório também registra a
restrição que impede um ganho muito maior, e por que ela não é contornável hoje.

## 1. O que mudou desde a investigação anterior

O [relatório de repasse](../s10_passthrough/report.md) fechou o espaço endógeno:
com preço e Brent apenas, o teto é ~6% sobre a persistência, e o modelo testado
perdeu no holdout. A conclusão foi que faltava informação, não arquitetura.

Esta rodada foi atrás da informação que faltava.

## 2. Fontes novas e por que cada uma

| fonte | conteúdo | situação anterior |
|---|---|---|
| ULSD (`HO=F`, NY Harbor) | futuro de diesel, USD/galão, diário | coluna 100% NaN — a fonte antiga devolvia página de verificação de robô |
| ANP produtores | preço semanal do Diesel S-10 na refinaria | ausente do projeto |
| Brent, dólar (IPEA) | diário | já existiam |

Tudo passa por [`21_s10_ingest_causal.py`](../../../scripts/21_s10_ingest_causal.py),
que baixa, alinha ao índice semanal da ANP e grava manifesto com SHA-256, número
de linhas e cobertura por fonte. Cobertura final: 702/702 semanas em todas as
colunas.

### 2.1 O preço de produtor é o sinal mais forte que existe — e chega tarde demais

A variação semanal do preço de refinaria correlaciona **+0,566** com a variação
da revenda na semana seguinte. É de longe o sinal mais forte medido neste
projeto: momentum dá +0,332, paridade ULSD +0,367, Brent +0,354.

Mas o próprio arquivo da ANP declara: *"a estimativa de atualização do arquivo
eletrônico disponibilizado é de doze dias após o encerramento da semana de
competência"*. Com a previsão emitida quando a revenda da semana anterior sai, o
dado só está disponível com três semanas de defasagem. E o sinal decai:

| defasagem | correlação com a variação da revenda | disponível em tempo real |
|---|---:|---|
| 1 semana | **+0,566** | não |
| 2 semanas | +0,224 | não |
| 3 semanas | +0,097 | sim |

Quantificado em walk-forward no desenvolvimento: com o produtor em lag 1 o ganho
sobre a persistência seria de **+13,7%**; com o lag 3 que a ANP entrega, +1,7% —
indistinguível do momentum sozinho.

**Esse é o teto real que resta, e ele está trancado por um atraso de publicação,
não por modelagem.** Destravá-lo exige capturar os anúncios da Petrobras no dia,
que são públicos mas não têm série baixável.

### 2.2 Um defeito de dados na fonte oficial

A coluna `Brasil` do arquivo de produtores apresenta valores impossíveis em 2026:
nas semanas de 20 e 27 de julho ela marca R$ 5,32/L enquanto quatro das cinco
regiões ficam em ~R$ 3,8/L — uma média ponderada não pode exceder quase todos os
seus componentes. O arquivo declara dados preliminares sujeitos a reprocessamento.

A ingestão usa a **mediana entre as cinco regiões**, que é imune a esses
episódios (desvio das variações semanais 0,114 contra 0,140 da coluna `Brasil`) e
está coberta por teste de regressão.

## 3. O modelo

Paridade de importação de diesel em R$/L, `ULSD ÷ 3,785411784 × USD/BRL`, com o
mesmo tratamento que funcionou antes: variação relativa do insumo multiplicada
pelo nível de preço vigente, estimação robusta de Huber, janela expansiva.

```
Δp(T) = a + b1·Δp(T−1) + b2·Δlog paridade(T−1)·p(T−1)
```

Coeficientes no ajuste completo (649 semanas): `dp1 +0,308`, `rpar1 +0,039`.

**Disponibilidade:** o índice semanal da ANP é datado pelo domingo que inicia a
semana, e as séries diárias são projetadas por `ffill`. O ULSD e o dólar na linha
`T` são o fechamento da sexta anterior ao início da semana — estritamente no
passado de toda a janela de medição. O teste `test_parity_panel_features_are_causal`
verifica que alterar o futuro não muda nenhum atributo do passado.

### 3.1 Seleção pela decisão, não pelo RMSE

O gate histórico do repositório não é decidível nesta série: uma semana responde
por 75% do erro quadrático do holdout. A seleção usou a economia da política de
compra e a precisão dos gatilhos como critério primário.

Desenvolvimento, 156 semanas (2021-08 a 2024-08):

| spec | RMSE | economia | gatilhos | precisão | maior evento |
|---|---:|---:|---:|---:|---:|
| **paridade** (`dp1`,`rpar1`) | 0,100760 | **R$ 47.169** | 44 | **70,5%** | **20,5%** |
| paridade_ecm | 0,099814 | R$ 47.169 | 50 | 68,0% | 20,5% |
| paridade_l2_ecm | 0,098949 | R$ 45.162 | 53 | 64,2% | 21,4% |
| paridade_l2_ecm_brent | **0,098946** | R$ 43.777 | 51 | 64,7% | 22,1% |
| ARIMA | 0,105056 | R$ 30.346 | 27 | 66,7% | 31,9% |

Especificações mais ricas melhoram o RMSE em ~2% — dentro do ruído documentado —
e **pioram** a precisão do gatilho. A escolhida é a mais simples: melhor economia,
melhor precisão, menor concentração num único evento, e positiva nos três folds
(R$ 32.169 / 4.846 / 3.808, contra R$ 18.000 / 3.923 / 2.077 do ARIMA).

O limiar de R$ 0,01/L foi mantido sem ajuste — a varredura de sensibilidade
mostrou que o valor pré-registrado já era o ótimo. A vantagem persiste com custo
de carregamento de até R$ 0,01/L/semana.

A especificação foi congelada em código
([`22_s10_parity_selection.py`](../../../scripts/22_s10_parity_selection.py),
`FROZEN_SPEC`) antes da leitura do holdout.

## 4. Holdout final — 104 semanas

| modelo | RMSE | MAE | direcional | economia | anualizada | CI90 inferior | gatilhos | precisão |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **paridade** | **0,080807** | 0,027521 | **71,8%** | **R$ 19.385** | **R$ 9.786** | **R$ 990** | 26 | 65,4% |
| ARIMA | 0,081463 | **0,027069** | 59,2% | R$ 16.962 | R$ 8.563 | R$ 117 | 8 | **75,0%** |
| persistência | 0,095630 | 0,032596 | — | — | — | — | 0 | — |

O modelo generalizou: venceu em RMSE, em acurácia direcional e em economia.

Leitura honesta dos números:

- **Acurácia direcional 71,8% contra 59,2%** é a diferença mais relevante. É a
  métrica que corresponde a "decidir certo na maioria das vezes".
- **Economia +14,3%**, com limite inferior de confiança de 90% positivo
  (R$ 990/ano contra R$ 117 do ARIMA) — ainda apertado, mas do lado certo.
- **A precisão do gatilho caiu**: 65,4% contra 75,0% do ARIMA. O modelo age três
  vezes mais (26 contra 8 gatilhos) e erra proporcionalmente mais, mas o saldo é
  positivo. Quem prioriza menos intervenções sobre mais economia deve subir o
  limiar; a R$ 0,03/L a precisão sobe para ~71% no desenvolvimento.
- **44% da economia veio de um único evento.** Menos concentrado que o ARIMA
  (50,3%), ainda material. O número não deve ser tratado como promessa.
- O ganho encolheu bastante do desenvolvimento (+55% de economia) para o holdout
  (+14%). Isso é esperado e é o motivo de o holdout existir.

### 4.1 Contagem de leituras do holdout

Esta é a **segunda leitura** do holdout neste projeto: a primeira foi o modelo de
repasse Brent, rejeitado. Duas leituras inflam o otimismo do resultado. A
confirmação prospectiva continua obrigatória antes de promoção.

### 4.2 Uma observação prospectiva

Treinado até 2026-08-09, o modelo prevê R$ 6,8879/L para a semana de 2026-08-16.
O valor oficial da ANP registrado pelo repositório para essa semana é R$ 6,89/L —
erro de R$ 0,0021/L, contra R$ 0,0081/L do ARIMA. É **uma** observação; não é
evidência, e está registrada apenas para iniciar a contagem prospectiva.

## 5. Recomendação

1. **Promover o modelo de paridade a primário**, com ARIMA como challenger e
   persistência como fallback final. Ele vence no holdout nas três métricas que
   importam para o produto.
2. **Manter o limiar de R$ 0,01/L** e expor o limiar como parâmetro do cliente:
   quem tolera menos intervenções escolhe R$ 0,03/L e troca economia por precisão.
3. **Acumular evidência prospectiva** — o holdout está gasto; só semanas futuras
   decidem daqui em diante.
4. **Perseguir os anúncios da Petrobras em tempo real.** É o único caminho
   conhecido para sair de +14% e chegar perto do +13,7% de RMSE que o produtor em
   lag 1 permite. Exige capturar comunicados no dia, com data e magnitude em R$/L.
5. **Não reabrir a busca por arquitetura.** Continua valendo o resultado anterior:
   boosting perde para regressão linear robusta nestes dados.

## 5.1 Registro prospectivo — o mecanismo que faltava

A recomendação 3 acima exige acumular evidência prospectiva, mas até 24/08/2026
não havia onde acumulá-la: `latest_forecast.json` é sobrescrito a cada execução,
então a previsão da semana anterior era destruída antes de poder ser comparada
com o valor oficial.

`23_s10_parity_production.py` agora grava cada previsão em `parity_ledger.jsonl`,
append-only e encadeado por SHA-256, e liquida a previsão pendente assim que a
semana-alvo dela aparece no painel. Cada liquidação registra o preço observado, o
erro do modelo, o erro da persistência, se o intervalo P10–P90 cobriu o
realizado, e o hash do registro de previsão que está sendo pontuado. Reexecutar o
script não conta a mesma semana duas vezes.

Contagem atual: **0/26 semanas liquidadas.** O ledger começa na previsão de
2026-08-23. A observação de 2026-08-16 descrita em §4.2 é anterior ao mecanismo e
não entra na contagem — ela continua valendo como o que sempre foi, uma
observação isolada registrada para iniciar o acompanhamento.

Primeira semana em disputa aberta, 2026-08-23, a partir de R$ 6,89/L observados
em 2026-08-16:

| modelo | previsão | direção | decisão da política |
|---|---:|---|---|
| paridade | R$ 6,9121/L (P10–P90 6,8310–7,0078) | alta de R$ 0,0221 | antecipar 11.538 L |
| ARIMA (produção) | R$ 6,8821/L | queda de R$ 0,0079 | não antecipar |

Os dois discordam do sinal. Uma semana não decide nada, mas discordância
direcional é o tipo de observação que acumula informação rápido — bem mais rápido
do que semanas em que ambos acertam por não acontecer nada.

## 6. Reprodução

```bash
python scripts/21_s10_ingest_causal.py                    # baixa e versiona as fontes
python scripts/22_s10_parity_selection.py --skip-holdout  # só desenvolvimento
python scripts/22_s10_parity_selection.py                 # abre o holdout
python scripts/23_s10_parity_production.py                # treina e emite a previsão
python -m pytest tests/test_causal_ingest.py tests/test_passthrough.py
```

Artefatos: `development_folds.csv`, `development_predictions.csv`,
`holdout_predictions.csv`, `holdout_comparison.csv`, `manifest.json`,
`latest_forecast.json`, `artifacts/s10_parity.joblib`.
