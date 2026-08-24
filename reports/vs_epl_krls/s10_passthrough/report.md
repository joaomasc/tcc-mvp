# Repasse causal para o S10 — diagnóstico, modelo e resultado

Data: 2026-08-24. Escopo: previsão de uma semana do preço médio nacional de
revenda do Diesel B S10.

**Conclusão: o ARIMA permanece primário. O modelo de repasse foi rejeitado no
holdout.** O valor deste trabalho está no diagnóstico, que explica por que o
programa de pesquisa do repositório está travado, e em oito hipóteses fechadas
com evidência.

## 1. Por que nenhum challenger passa nos gates

### 1.1 O RMSE tem tamanho amostral efetivo de aproximadamente 3

No holdout de 104 semanas, a concentração do erro quadrático do ARIMA é:

| | % do SSE |
|---|---:|
| pior 1 semana | **75,1%** |
| piores 3 semanas | 91,2% |
| piores 10 semanas | 96,3% |

A semana de 2026-03-08 (R$ 6,15 → 6,89) sozinha responde por três quartos do
erro. Um gate de "ganho de 2% no RMSE" e um teste Diebold–Mariano aplicados a
essa amostra estão sendo decididos por um punhado de observações. O `p = 0,1338`
do ARIMA contra a persistência não indica que o ARIMA seja fraco; indica que o
teste não tem poder. Qualquer comparação futura de modelos nesta série precisa
usar métricas robustas e decomposição por regime, não RMSE agregado.

### 1.2 Em dois terços das semanas, a persistência ganha de todo mundo

| regime | ARIMA | pass-through | persistência |
|---|---:|---:|---:|
| semanas paradas (dev) | 0,02200 | 0,02057 | **0,01180** |
| semanas de evento (dev) | 0,14253 | **0,13688** | 0,15672 |

Modelar acrescenta ruído onde nada acontece. Esse é um fato estrutural da série,
não um defeito de um modelo específico.

### 1.3 O teto endógeno é ~6% e já foi alcançado

Walk-forward honesto no período de desenvolvimento:

| preditor | RMSE | ganho vs persistência |
|---|---:|---:|
| persistência | 0,08420 | — |
| momentum (o que o ARIMA explora) | 0,08266 | +1,8% |
| oráculo que sabe *se* haverá evento | — | +1,5% |
| oráculo que sabe o *tamanho* do salto | 0,00685 | +90% |

Saber que um evento vem quase não vale nada; todo o valor está na magnitude, e a
magnitude não está na série de preço. **Nenhuma mudança de arquitetura quebra
esse teto** — o limite é de informação, não de capacidade. O teste com
gradient boosting abaixo confirma isso empiricamente.

## 2. Três defeitos de dados encontrados

1. **`ulsd` é 100% NaN.** [`download.py:67`](../../../src/data/download.py) baixa
   de stooq, que hoje responde com uma página de verificação de robô;
   [`build.py:98`](../../../src/data/build.py) trata a falha como série vazia e
   preenche NaN silenciosamente. Todas as colunas `ulsd_l1..l12` são inúteis. O
   ULSD é o benchmark *de diesel* e seria melhor proxy que o Brent (petróleo cru).
2. **`petrobras_reajuste` não é dado da Petrobras.**
   [`build.py:129`](../../../src/data/build.py) define a coluna como
   `salto no próprio preço | |paridade_z| > 2`. É um detector derivado da série
   alvo, não informação externa: AUC de 0,19 para prever evento na semana
   seguinte, pior que o acaso. A documentação a descreve como atributo causal
   externo; ela não é.
3. **`distribuicao` termina em 2020-08-16.** O preço de distribuição é um
   indicador antecedente real (corr +0,277 com a variação seguinte da revenda) e
   está indisponível há seis anos.

## 3. O modelo de repasse

### 3.1 Especificação

Alvo `y(T) = p(T) − p(T−1)` em R$/L, previsto na origem `T−1`:

```
y(T) = a + b1·y(T−1) + b2·Δlog custo(T−1)·p(T−1)
                    + b3·Δlog custo(T−2)·p(T−1)
                    + g·z_coint(T−1)·p(T−1)
```

onde `custo = brent × usdbrl`, e `z_coint` é o resíduo padronizado da regressão
de cointegração `log p ~ log custo` estimada em janela expansiva. A estimação usa
IRLS de Huber (δ = 3,5).

Duas decisões carregaram quase todo o ganho de desenvolvimento:

- **Escala econômica.** Multiplicar a variação *relativa* do insumo pelo nível de
  preço vigente converte o repasse em R$/L. Numa série cujo nível triplicou, usar
  a variação relativa crua trata 1% em 2013 e 1% em 2026 como o mesmo evento.
  Isso sozinho levou o RMSE médio de dev de 0,10274 para 0,10072.
- **Estimação robusta.** Mínimos quadrados são dominados pelas poucas semanas de
  choque, o que distorce os coeficientes para as outras 95%. Huber corrigiu isso.

### 3.2 Auditoria de timing

O índice semanal da ANP é datado pelo domingo que **inicia** a semana pesquisada,
e o resample do painel usa `ffill`. Portanto `brent_brl` na linha `T` é o
fechamento da sexta anterior ao início da semana `T`: está estritamente no
passado de toda a janela de medição do preço. O repasse observado leva cerca de
duas semanas, então as defasagens 1 e 2 concentram o sinal — a coluna `brent_l1`
que já existe no repositório tem o timing correto.

Achado de processo: **o conjunto de atributos exógenos nunca entrou na seleção
de produção.** [`05_s10_model_selection.py:203`](../../../scripts/05_s10_model_selection.py)
constrói apenas `price`, `lags` e `dynamics`. O campeão de produção foi escolhido
sem jamais ver Brent ou câmbio.

O teste `test_features_are_causal` verifica que alterar o futuro não muda nenhum
atributo do passado.

### 3.3 Desenvolvimento: o modelo ganha

Três folds expansivos de 52 semanas, seleção feita apenas aqui.

| modelo | RMSE médio | pior fold | MAE | pior razão vs persistência |
|---|---:|---:|---:|---:|
| **pass-through** | **0,100575** | 0,158057 | **0,050127** | **0,9435** |
| ARIMA | 0,105056 | 0,165437 | 0,052744 | 0,9876 |
| persistência | 0,114094 | 0,167514 | 0,055949 | 1,0000 |

Ganho de **4,27% sobre o ARIMA**, vencendo em cada um dos três folds
individualmente, e batendo a persistência em todos eles.

### 3.4 Holdout: o modelo perde

Leitura única das 104 semanas finais, feita depois de congelar a especificação.

| modelo | RMSE | MAE | RMSE parado | RMSE evento | razão vs persistência |
|---|---:|---:|---:|---:|---:|
| **ARIMA** | **0,081463** | **0,027069** | **0,011787** | 0,139446 | 0,8519 |
| pass-through | 0,082861 | 0,028919 | 0,021819 | 0,139511 | 0,8665 |
| persistência | 0,095630 | 0,032596 | 0,008597 | 0,164404 | 1,0000 |

O modelo ficou **1,7% pior que o ARIMA**. A decomposição mostra exatamente onde:
nas semanas de evento os dois empatam (0,13951 contra 0,13945), mas nas semanas
paradas o pass-through erra quase o dobro (0,02182 contra 0,01179). Ele continua
reagindo ao Brent quando nada é repassado.

No período do holdout o preço ficou longos trechos literalmente constante. O
ARIMA, com diferenciação, converge para deriva quase nula e se aproxima da
persistência nesses trechos; o modelo de repasse não.

Política de compra (200 mil L/mês, antecipar 25% quando a alta prevista supera
R$ 0,01/L):

| modelo | economia líquida | gatilhos | precisão |
|---|---:|---:|---:|
| ARIMA | R$ 16.962 | 8 | 75,0% |
| pass-through | R$ 7.962 | 21 | 52,4% |

O modelo dispara quase três vezes mais e acerta muito menos — a mesma
reatividade excessiva, medida na moeda do produto.

Testes: bootstrap em blocos `p = 0,056` para pass-through contra ARIMA
(evidência limítrofe de que é *pior*), `p = 0,263` contra persistência.

## 4. Hipóteses testadas e rejeitadas

Todas avaliadas nos folds de desenvolvimento, salvo indicação contrária.

| hipótese | resultado | veredito |
|---|---|---|
| gradient boosting sobre os mesmos atributos | RMSE 0,10304 mas perde da persistência num fold (razão 1,004) e MAE 12% pior | rejeitado — capacidade extra não ajuda |
| portão de regime na previsão pontual | melhora semana parada (0,0206→0,0150) mas piora evento (0,1369→0,1499); pior em RMSE e MAE | rejeitado |
| zona morta sobre o ARIMA | pior monotonicamente; economia cai de R$ 28.096 para R$ 17.504 | rejeitado |
| encolhimento por limiar suave | pior monotonicamente (λ=0 é ótimo) | rejeitado |
| alvo padronizado por volatilidade | 0,10352 contra 0,10072 | rejeitado |
| repasse assimétrico ("rockets and feathers") | 0,10204 contra 0,10072 | rejeitado |
| intervalo por mistura de dois regimes | cobertura 64,7% para nominal 80% | rejeitado |
| escala de intervalo log-linear | cobertura 72,4%, largura de evento explode para 0,937 | rejeitado |
| intervalo condicional sobre o ARIMA | *interval score* 0,3924 contra 0,3868 do incumbente | rejeitado |

A nota sobre o intervalo condicional merece detalhe. Ele calibra melhor
(cobertura 78,2% contra 73,1% para nominal 80%) e responde ao regime (largura de
evento 1,23× a de semana parada, contra 1,02× do incumbente). Mas pela regra de
pontuação própria — *interval score* de Winkler, que pune largura e não-cobertura
ao mesmo tempo — ele não vence. Comparar só cobertura ou só largura escolheria o
intervalo errado. O componente ficou no repositório, testado e documentado, com o
resultado negativo registrado.

## 5. Recomendação

1. **Manter o ARIMA como primário.** Nada testado aqui o supera fora da amostra.
2. **Parar de buscar ganho de RMSE pontual com dados endógenos + Brent.** O teto
   está demonstrado e foi atingido. O próximo ganho material exige dados causais
   estruturados que o projeto não tem: anúncios de reajuste da Petrobras com data
   e magnitude em R$/L, ICMS ad rem (CONFAZ), PIS/COFINS, e a mistura obrigatória
   de biodiesel (CNPE). Todos são datados e públicos antes de chegarem à bomba.
3. **Corrigir os três defeitos de dados** da seção 2 antes de qualquer nova
   pesquisa; dois deles falham em silêncio.
4. **Trocar os gates de promoção.** RMSE agregado com `n` efetivo 3 não é
   decidível. Usar MAE, métricas por regime, *interval score* e bootstrap em
   blocos, e tratar a economia da política de compra como KPI primário.
5. **Registrar que o holdout foi lido uma vez** por este experimento. Ele está
   mais gasto do que antes; leituras futuras devem ser contadas.

## 6. Reprodução

```bash
python scripts/19_s10_passthrough_selection.py --skip-holdout   # só desenvolvimento
python scripts/19_s10_passthrough_selection.py                  # abre o holdout
python scripts/20_s10_conditional_interval.py --skip-holdout
python -m pytest tests/test_passthrough.py
```

Artefatos: `development_folds.csv`, `development_predictions.csv`,
`holdout_predictions.csv`, `holdout_comparison.csv`, `manifest.json`.
