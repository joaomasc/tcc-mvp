# VS-ePL-KRLS em Python

Implementação independente, pequena e prequential do **Variable Step-Size evolving Participatory Learning with Kernel Recursive Least Squares** para regressão online e previsão de séries temporais. A biblioteca cria, atualiza e funde regras fuzzy durante o fluxo e mantém um consequente KRLS esparso separado por regra.

O pacote novo é `vs_epl_krls`. O pacote legado `vsepl_krls` continua no repositório apenas para comparação e para não quebrar os scripts e testes históricos; ele não é usado pelo novo bundle de produção.

> Estado: a biblioteca VS-ePL-KRLS é uma implementação de pesquisa, não uma reprodução bit a bit certificada. Para a aplicação S10 de uma semana, existe um bundle operacional versionado: ARIMA é o primário aprovado e VS-ePL-KRLS permanece challenger em shadow mode porque não passou os gates de promoção.

> Atualização de 24/08/2026: um **modelo de paridade de importação de diesel** superou o ARIMA no holdout final e é o novo candidato a primário — RMSE 0,080807 contra 0,081463, acurácia direcional 71,8% contra 59,2% e economia de R$ 19.385 contra R$ 16.962 na política de compra. Veja [Modelo de paridade](#modelo-de-paridade-de-diesel).

## Modelo de paridade de diesel

O diagnóstico que motivou este modelo está em [reports/vs_epl_krls/s10_passthrough/report.md](reports/vs_epl_krls/s10_passthrough/report.md): no holdout de 104 semanas, **uma única semana responde por 75,1% do erro quadrático do ARIMA**, o que torna o gate histórico (2% de ganho em RMSE, Diebold–Mariano abaixo de 5%) indecidível. Com preço e Brent apenas, o teto sobre a persistência é de ~6% e já estava atingido; o valor está na *magnitude* dos saltos, que não vem da série de preço.

Três fontes causais novas entraram, todas automatizadas com manifesto e SHA-256 por arquivo:

| fonte | conteúdo | situação anterior |
|---|---|---|
| ULSD (`HO=F`) | futuro de diesel, USD/galão, diário | coluna 100% NaN — a fonte antiga devolvia página de verificação de robô e a falha era engolida |
| ANP produtores | preço semanal do Diesel S-10 na refinaria | ausente do projeto |
| Brent, dólar (IPEA) | séries diárias | já existiam |

O modelo usa a paridade de importação em R$/L, `ULSD ÷ 3,785411784 × USD/BRL`, com a variação relativa do insumo multiplicada pelo nível de preço vigente e estimação robusta de Huber em janela expansiva:

```text
Δp(T) = a + b1·Δp(T−1) + b2·Δlog paridade(T−1)·p(T−1)
```

A especificação foi escolhida **pela economia da política de compra**, não pelo RMSE, e congelada em código antes da leitura do holdout.

| holdout, 104 semanas | paridade | ARIMA | persistência |
|---|---:|---:|---:|
| RMSE | **0,080807** | 0,081463 | 0,095630 |
| acurácia direcional | **71,8%** | 59,2% | — |
| economia líquida | **R$ 19.385** | R$ 16.962 | — |
| CI90 inferior anual | **R$ 990** | R$ 117 | — |
| precisão do gatilho | 65,4% (26) | **75,0%** (8) | — |

Ressalvas que acompanham o número: a precisão do gatilho é menor porque o modelo age três vezes mais; 44% da economia veio de um único evento; e esta foi a **segunda leitura do holdout** no projeto, o que infla otimismo. Confirmação prospectiva continua obrigatória.

```bash
python scripts/21_s10_ingest_causal.py                    # baixa e versiona as fontes
python scripts/22_s10_parity_selection.py --skip-holdout  # só desenvolvimento
python scripts/23_s10_parity_production.py                # treina e emite previsão + decisão
```

O ganho que continua fora de alcance está registrado em [reports/vs_epl_krls/s10_parity/report.md](reports/vs_epl_krls/s10_parity/report.md): a variação do preço de refinaria correlaciona **+0,566** com a variação seguinte da revenda, mas a ANP publica o arquivo ~12 dias após o fim da semana, e na defasagem utilizável restam +0,097. Capturar os anúncios da Petrobras no dia levaria de +1,7% para +13,7% de ganho sobre a persistência.

## Produto S10 Intelligence

O repositório agora também contém uma camada de produto API-only para piloto controlado. Ela carrega somente releases imutáveis verificadas por SHA-256, bloqueia previsões vencidas e expõe previsão, catálogo dos modelos, evidências, cenários, health/readiness e métricas. Não há frontend customizado.

```powershell
python -m pip install -e ".[production,service,test]"
python scripts\16_s10_procurement_backtest.py
python scripts\17_build_investor_package.py
python scripts\15_s10_service.py
```

Use `http://127.0.0.1:8000/v1/models` para o catálogo dos modelos, `/v1/forecast` para a previsão e `/v1/evidence` para a avaliação congelada. A raiz retorna apenas metadados JSON e `/openapi.json` entrega o contrato de máquina. Swagger e ReDoc permanecem desativados em todos os ambientes; em `S10_ENVIRONMENT=production`, `S10_API_KEY` é obrigatória. A API é deliberadamente somente leitura: atualização e promoção de modelos permanecem fora do caminho de requisição.

Release operacional mais recente:

- observação oficial ANP de 16–22/08/2026: R$ 6,89/L, 3.173 postos, fonte e arquivo registrados por hash;
- erro prospectivo do ARIMA: R$ 0,0081/L; híbrido: R$ 0,0091/L; persistência: R$ 0,0200/L;
- nova previsão para a semana de 23/08/2026: R$ 6,882/L, P10–P90 de R$ 6,819 a R$ 6,939/L;
- shadow: 1/26 resultados mínimos; promoção automática continua proibida;
- replay causal pré-fixado para 200 mil L/mês: R$ 16.962 no holdout de 104 semanas, equivalente a R$ 8.563/ano; 50,3% do ganho veio do maior evento, portanto o número não deve ser tratado como promessa comercial.

Consulte [product_readiness_2026-08-24.md](docs/product_readiness_2026-08-24.md), [investor_brief.md](docs/investor_brief.md), [architecture.md](docs/architecture.md) e [security.md](docs/security.md).

## Referências

- Queiroz et al., “Variable step-size evolving participatory learning with kernel recursive least squares applied to gas prices forecasting in Brazil”: [artigo aberto](https://pmc.ncbi.nlm.nih.gov/articles/PMC8147597/), [DOI](https://doi.org/10.1007/s12530-021-09388-z) e [Springer](https://link.springer.com/article/10.1007/s12530-021-09388-z).
- Dissertação com o Algoritmo 1 e as equações detalhadas: [PUC-Rio/Maxwell](https://www.maxwell.vrac.puc-rio.br/52507/52507.PDF).
- Versão em português: [Congresso Brasileiro de Automática](https://ojs.sba.org.br/index.php/cba/article/download/1039/1030/2819).
- API de referência arquitetural, não copiada: [evolvingfuzzysystems](https://github.com/kaikerochaalves/evolvingfuzzysystems). Esse projeto é GPL-3.0; esta implementação foi escrita de forma independente sob MIT.
- KRLS esparso e critério de dependência linear aproximada: [Engel, Mannor e Meir, 2004](https://citeseerx.ist.psu.edu/document?doi=ed5d2aca56aa23f846e793160373bc74a431431c&repid=rep1&type=pdf).
- Cobertura online sob mudanças de distribuição como referência para evolução futura dos intervalos: [Bhatnagar et al., ICML 2023](https://proceedings.mlr.press/v202/bhatnagar23a.html). O bundle atual usa quantis em janela móvel, não afirma implementar SAOCP.

Ao publicar resultados, cite o artigo original. A licença desta implementação não altera os direitos sobre o método ou os trabalhos acadêmicos.

## Diferenças entre os modelos

| Modelo | Antecedente evolutivo | Consequente | Diferencial |
|---|---|---|---|
| ePL | aprendizado participativo | RLS linear | excitação controla criação/atualização de regras |
| ePL-KRLS | ePL | KRLS não linear | dicionário de kernels por regra |
| ePL-KRLS-DISCO | família ePL-KRLS | KRLS | acrescenta mecanismos baseados em correlação de distância; não é VS-ePL-KRLS |
| VS-ePL-KRLS | ePL-KRLS | KRLS | adapta `beta` pelo erro a cada observação |

## Equações implementadas

Para entrada normalizada `x` com `m` atributos e centro `v_i`, a compatibilidade é

```text
rho_i(k) = clip(1 - ||x(k) - v_i(k)|| / m, 0, 1)
```

A excitação usa o `beta` do passo anterior:

```text
a_i(k) = a_i(k-1) + beta(k-1) [1 - rho_i(k) - a_i(k-1)]
```

Na convenção formal da dissertação, `tau(k)=beta(k-1)` e `gamma(k)=1-beta(k-1)`. Uma regra nasce quando `min_i a_i(k) > tau(k)`. Caso contrário, a regra de maior compatibilidade é atualizada. Limiares fixos podem ser passados explicitamente para estudar a convenção alternativa sugerida pelos valores iniciais da tabela do artigo.

O passo variável é

```text
se |erro_normalizado(k)| > error_threshold:
    beta(k) = beta(k-1) / alpha_vs1
senão:
    beta(k) = beta(k-1) * alpha_vs2
beta(k) = clip(beta(k), beta_min, beta_max)
```

Cada saída local é uma expansão RBF:

```text
y_i(x) = sum_j theta_ij exp(-||x-d_ij||² / (2 nu_ij²))
```

A saída global é a soma das saídas locais ponderadas por `rho_i / sum(rho)`. O critério de novidade usa `psi=min_j ||x-d_ij||` e `delta=novelty_factor*nu_nearest`; por padrão `novelty_factor=0.1`.

O relatório [docs/implementation_report.md](docs/implementation_report.md) separa as fórmulas extraídas das fontes das decisões de engenharia.

## Instalação

Python 3.10 ou superior:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[experiments,production,test]"
```

Para instalar somente as dependências deste trabalho sem instalar o pacote:

```bash
python -m pip install -r requirements-vs-epl-krls.txt
```

O `requirements.txt` da raiz permanece mais amplo porque também sustenta os benchmarks e o pipeline legado deste repositório.

## Uso mínimo

```python
from vs_epl_krls import VSEPLKRLS

model = VSEPLKRLS(
    error_threshold=0.003,
    alpha_vs1=0.85,
    alpha_vs2=0.80,
    max_dictionary_size=40,
)

for x_t, y_t in stream:                    # x_t deve estar em [0, 1]
    y_hat_t = model.predict_one(x_t)        # não altera estado
    same_y_hat = model.learn_one(x_t, y_t) # prevê primeiro, aprende depois

print(model.n_rules)
print(model.get_rules())
print(model.get_history()[-1])
```

Também estão disponíveis `fit(X, y)`, `predict(X)`, `reset()`, `summary()` e a ablação `EPLKRLSFixedBeta`.

## Ordem do aprendizado online

1. valida `x_t` e calcula compatibilidades e ativações;
2. calcula as saídas KRLS locais e `y_hat_t`, sem consultar `y_t`;
3. recebe `y_t`, calcula erro e sua normalização configurada;
4. atualiza as excitações com `beta_(t-1)`;
5. calcula o novo `beta_t` e aplica os limites;
6. usa `tau_t=beta_(t-1)` e `gamma_t=1-beta_(t-1)` para criar, atualizar ou fundir;
7. atualiza o antecedente e o KRLS da regra vencedora, ou inicializa a regra nova;
8. registra erro, `beta`, regras, ações e tamanhos dos dicionários.

Essa ordem resolve uma ambiguidade de apresentação do Algoritmo 1: o erro necessário ao passo variável só existe depois da saída global, embora a saída global seja impressa no final do pseudocódigo. A API força a semântica prequential.

## Hiperparâmetros

### Passo variável e erro

| Parâmetro | Padrão | Função |
|---|---:|---|
| `beta_initial` | 0.18 | velocidade inicial da excitação |
| `beta_min`, `beta_max` | 0.0001, 0.999 | limites de `beta` |
| `alpha_vs1`, `alpha_vs2` | 0.97, 0.84 | divisão em erro alto e multiplicação em erro baixo |
| `beta_recovery_rate` | 0.0 | extensão opcional que tira `beta` do piso sob erro alto; zero preserva a equação publicada |
| `error_threshold` | 0.001 | `gamma_bar` do passo variável |
| `error_normalization` | `none` | `none`, `fixed`, `running_range` ou `running_std` |
| `error_scale` | 1.0 | denominador do modo `fixed` |
| `error_scale_epsilon` | 1e-8 | proteção contra divisão por zero |
| `variable_beta` | `True` | desativa o VS quando falso |

### Regras fuzzy

| Parâmetro | Padrão | Função |
|---|---:|---|
| `alpha` | 0.01 | aprendizado do centro |
| `arousal_threshold` | `None` | `None` usa `beta_(t-1)`; número fixa `tau` |
| `compatibility_threshold` | `None` | gatilho opcional adicional de baixa compatibilidade |
| `merge_threshold` | `None` | `None` usa `1-beta_(t-1)`; número fixa `gamma` |
| `enable_rule_merging` | `True` | habilita fusões |
| `max_rules` | 20 | limite de regras |
| `center_update` | `paper` | equação literal ou alternativa `compatibility` |
| `initial_rule_dispersion` | 0.05 | dispersão diagonal inicial |
| `min_rule_dispersion` | 1e-6 | piso numérico |

### KRLS

| Parâmetro | Padrão | Função |
|---|---:|---|
| `kernel_sigma` | 0.5 | largura RBF inicial `nu_0` |
| `regularization` | 1e-4 | regularização `lambda` |
| `novelty_factor` | 0.1 | multiplicador de `delta` |
| `max_dictionary_size` | 40 | limite por regra |
| `replacement_strategy` | `oldest` | `oldest`, `least_used` ou `none` |
| `forgetting_factor` | 1.0 | memória do RLS de dicionário fixo |
| `dictionary_usage_decay` | 1.0 | decaimento da utilidade usada pela substituição `least_used` |
| `adapt_kernel_width` | `True` | atualização recursiva de `nu` |
| `min_kernel_width`, `max_kernel_width` | 0.001, 10.0 | limites de largura |
| `max_width_relative_change` | 0.1 | limite por passo |
| `replay_capacity` | 256 | janela para reconstruções estáveis |

### Entrada e operação

| Parâmetro | Padrão | Função |
|---|---:|---|
| `input_bounds` | `(0, 1)` | domínio exigido pela compatibilidade original |
| `clip_inputs` | `False` | se verdadeiro, recorta valores fora do domínio |
| `initial_prediction` | 0.0 | saída antes da primeira regra |
| `log_events` | `False` | emite eventos pelo `logging` padrão |
| `random_state` | `None` | reservado e serializado; o algoritmo atual é determinístico |

## Experimento sintético

```bash
python examples/synthetic_regression.py --random-state 42
```

O fluxo tem 480 observações, relação não linear, ruído e mudança de regime na amostra 240. O script compara o passo variável com `EPLKRLSFixedBeta`, mede MSE/RMSE/MAE/SMAPE, tempo, criações/fusões e dicionários, e grava:

- `reports/vs_epl_krls/synthetic/metrics.csv` e `metrics.json`;
- `trace.csv` com predições, erros, `beta`, regras e dicionários;
- `synthetic_regression.png`.

O resultado medido na máquina desta execução está registrado no próprio CSV; não é uma afirmação geral de superioridade.

| Modelo | RMSE | MAE | SMAPE | Tempo online | Máx. regras |
|---|---:|---:|---:|---:|---:|
| VS-ePL-KRLS | 0.12133 | 0.08850 | 19.69% | 1.92 s | 5 |
| ePL-KRLS beta fixo | 0.21271 | 0.15901 | 35.56% | 3.84 s | 3 |
| Persistência | **0.03527** | **0.02818** | **6.36%** | — | — |

O passo variável superou sua ablação nesse fluxo, mas a persistência foi muito melhor. Isso impede usar o experimento sintético como evidência de superioridade operacional do modelo.

## Pipeline ANP somente S10

O exemplo **não baixa nem inventa dados**. Obtenha um CSV real no [portal de dados abertos da ANP](https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos) ou no [catálogo dados.gov.br](https://dados.gov.br/dados/organizacoes/visualizar/agencia-nacional-do-petroleo-gas-natural-e-biocombustiveis-anp). O CSV precisa ter data, descrição do produto e preço; nomes não usuais podem ser informados explicitamente:

```bash
python examples/fuel_price_forecasting.py \
  --csv caminho/serie_anp.csv \
  --date-column DATA \
  --product-column PRODUTO \
  --price-column PRECO_MEDIO_REVENDA \
  --products S10 \
  --horizons 2 4
```

Planilhas oficiais `.xlsx` também são aceitas. O fluxo operacional filtra exclusivamente o Diesel B S10; diesel genérico e S500 ficam fora do escopo.

No PowerShell, substitua `\` por crase ou use uma linha única. O pipeline:

- reconhece S10, valida preços e datas e agrega semanalmente;
- cria `lags` sem usar observações futuras;
- divide cronologicamente;
- ajusta os escalonadores somente ao treino;
- só aprende o alvo de uma origem quando ele estaria disponível após o horizonte;
- compara com persistência e grava tabelas, predições e gráficos.

Os parâmetros de 2 e 4 semanas reportados para S10 na dissertação são usados no exemplo de reprodução. Para produção foi feita uma seleção separada de horizonte de uma semana, sem usar o holdout para escolher hiperparâmetros.

### Seleção profissional para uma semana

```bash
python scripts/05_s10_model_selection.py --horizon 1
python scripts/06_train_s10_production.py
python scripts/07_s10_predict.py --output reports/vs_epl_krls/s10_production/latest_forecast.json
```

Contrato: preço médio nacional semanal de revenda, 702 observações de 2012-12-30 a 2026-08-09, três folds expansivos de 52 semanas (156 pontos) para seleção/calibração e holdout final de 104 semanas. Todos os escalonadores são ajustados apenas no passado de cada fold e os alvos são revelados com atraso do horizonte.

| Modelo | RMSE holdout | MAE | SMAPE | RMSE / persistência | Direção | DM p-valor |
|---|---:|---:|---:|---:|---:|---:|
| ARIMA (primário) | **0.08145** | **0.02706** | **0.4121%** | **0.8517** | 59,2% | 0.1338 |
| ensemble | 0.08421 | 0.02852 | 0.4329% | 0.8806 | **78,9%** | 0.1205 |
| VS-ePL-KRLS | 0.09382 | 0.03360 | 0.5087% | 0.9810 | 63,4% | **0.0395** |
| persistência | 0.09563 | 0.03260 | 0.4898% | 1.0000 | 0,0% | 1.0000 |
| Ridge | 0.10694 | 0.03955 | 0.5896% | 1.1182 | 38,0% | 0.0716 |

O VS selecionado usa lags de preço e alvo `delta`, tem latência interna p95 de 1,55 ms, venceu a persistência nos três folds e ganhou 1,90% de RMSE no holdout com `p=0,0395`. A ampliação de capacidade eliminou a pressão de regras (13/20), mas o dicionário chegou a 20/20 e `beta` permaneceu quase sempre no piso. Como o ganho ficou ligeiramente abaixo do gate pré-fixado de 2% e o ARIMA continua muito melhor, o VS não foi promovido. O ARIMA teve ganho prático de 14,8% no RMSE; seu p-valor de 0,1338 ainda exige rollout monitorado, e não uma alegação de superioridade estatística. O bundle 1.1 completo tem 1,49 MiB e latência end-to-end p95 de 15,28 ms nesta máquina.

O intervalo P10–P90 calibrado exclusivamente nos folds obteve cobertura de 92,3% no holdout para nominal de 80%: é conservador e deve ser recalibrado quando a cobertura móvel sair da faixa operacional. O bundle, o hash, a previsão e o model card ficam em `artifacts/s10_production.joblib` e `reports/vs_epl_krls/s10_production/`. O procedimento semanal e os critérios de rollback estão em [docs/s10_production_runbook.md](docs/s10_production_runbook.md).

### Pesquisa do próximo challenger sem reabrir o holdout

```bash
python scripts/08_s10_next_challenger.py
```

Foram avaliadas, somente nos três folds de desenvolvimento, recuperação de `beta`, esquecimento KRLS, dicionários maiores com utilidade recente, atributos causais defasados de Brent/câmbio/reajuste e um híbrido que aprende online o resíduo do ARIMA. Nenhuma extensão direta superou com robustez o VS congelado. O melhor resultado médio do híbrido de lags reduziu o RMSE médio, mas piorou um fold em 7,3% e foi rejeitado pelo gate de estabilidade.

O candidato estável para **shadow research** foi `hybrid_dynamics_conservative`: correção residual com peso 0,5 e limite de R$ 0,10/L, RMSE médio 0,10456 contra 0,10506 do ARIMA, razão média 0,9946 e pior razão 0,9981. Ele venceu por margem pequena nos três folds, mas teve 34,4% de substituições KRLS. Não houve promoção nem nova leitura do holdout; são necessárias semanas futuras ainda não observadas. Resultados completos: [reports/vs_epl_krls/s10_next/report.md](reports/vs_epl_krls/s10_next/report.md).

O bundle operacional foi elevado ao contrato `1.1.0`: limita a calibração aos 156 resíduos mais recentes, incorpora o resíduo realizado após `update_one`, mede cobertura/MAE online, alerta undercoverage após 20 observações, registra churn do dicionário e rejeita artefatos 1.0. O primário continua ARIMA.

### Experimento prospectivo congelado

O próximo passo já foi iniciado com o candidato `hybrid_dynamics_conservative`, sem alterar o primário:

```bash
# leitura idempotente do forecast pendente
python scripts/09_s10_shadow.py

# quando o valor oficial da data-alvo chegar, preserve o artefato anterior
python scripts/09_s10_shadow.py \
  --update-date AAAA-MM-DD \
  --update-price VALOR_OFICIAL \
  --output-artifact artifacts/s10_shadow_hybrid_SEMANA.joblib
```

O freeze usa corte em 2026-08-09 e fingerprint de candidato `7410bb7e…cfd6a7`. A primeira realização oficial, 2026-08-16 a R$ 6,89/L, já foi incorporada; o artefato imutável atual tem SHA-256 `d9da2b3d…e52345a` e previsão pendente de R$ 6,8824/L para 2026-08-23. O ledger JSONL é encadeado por SHA-256; cada atualização exige corresponder exatamente ao `forecast_id` e à data-alvo anterior.

O status permanece `collecting`, agora com 1/26 resultados mínimos e 1/52 preferenciais. Mesmo quando os gates forem satisfeitos, `automatic_promotion_allowed` permanece falso: o máximo possível é `eligible_for_human_review`. O artefato shadow e seu ledger são independentes da release primária.

### Challenger com notícias operacionais

O corpus de notícias foi reaudidado com contato operacional usado apenas em memória. ANP, IBGE, MME e Fazenda produziram 5.752 registros entre 2014-08-08 e 2026-08-07; Petrobras permaneceu bloqueada. O snapshot semanal `weekly-signal.v3` tem 2.089 pares de origem/horizonte e SHA-256 `523a8d50…c120c9`.

```bash
python scripts/10_s10_news_backtest.py \
  --news-signals CAMINHO/weekly-signal/v3
```

O experimento usa somente os três folds congelados de desenvolvimento. O consumidor verifica ponteiro, manifesto, hashes, esquema, contagens e alinhamento ANP antes de anexar os atributos. Dois pares que não representavam uma semana real (`2015-08-09→2015-08-23` e `2020-08-16→2020-10-18`) foram removidos de todos os candidatos.

Nenhum candidato de notícias passou o gate. O híbrido atual obteve RMSE médio 0,104741; a melhor variante de impacto obteve 0,104926, uma piora de aproximadamente 0,18%, embora MAE e SMAPE tenham melhorado levemente. Assim, notícias permanecem como challenger de pesquisa e não alteram ARIMA, o bundle de produção ou o shadow atual. Consulte [docs/news_integration.md](docs/news_integration.md) e [reports/vs_epl_krls/s10_news/report.md](reports/vs_epl_krls/s10_news/report.md).

O classificador textual causal seguinte obteve 60,3% de acurácia, 52,3% de acurácia balanceada e macro-F1 de 52,3% no melhor canal (`pressure_domain_28d`), mas também não melhorou o forecast: RMSE 0,105018 contra 0,104741 e churn de 46,9%. Ele permanece pesquisa, com `selected_for_future_shadow=null` e sem acesso ao holdout.

```bash
python scripts/11_s10_news_pressure_backtest.py \
  --news-records CAMINHO/news-record/v2

python scripts/12_prepare_news_annotations.py \
  --news-records CAMINHO/news-record/v2
```

Foi preparado um lote cego e rastreável de 300 matérias para dois anotadores independentes. O uso em treino permanece bloqueado até preenchimento, concordância e adjudicação. Veja [protocolo de anotação](docs/news_annotation_protocol.md) e [relatório textual](reports/vs_epl_krls/s10_news_pressure/report.md).

A dupla anotação também foi simulada por duas políticas determinísticas. Após calibração, κ de relevância foi 0,912, mas o gate permaneceu fechado porque não houve cobertura suficiente das classes `up`, `down` e intensidades altas. Esses rótulos são úteis para testar o workflow, não para substituir especialistas nem treinar produção.

## Testes

```bash
python -m pytest tests/test_kernels.py tests/test_krls.py \
  tests/test_rule_evolution.py tests/test_variable_beta.py \
  tests/test_online_learning.py tests/test_fuel_pipeline.py \
  tests/test_s10_selection.py tests/test_s10_production.py

python -m pytest
python -m pytest --cov --cov-report=term-missing --cov-report=xml
```

A execução final teve **215 testes aprovados, 2 opcionais ignorados e 90,05% de cobertura**. A suíte verifica kernel, inserção em bloco, atualização recursiva, limite/substituição, singularidade, criação/fusão, passo variável, ausência de vazamento, dados constantes, NaN/Inf, `pickle`, serialização atômica, rejeição de versão antiga, determinismo, concorrência, guardrails residuais, cobertura móvel, cadência, avaliação atrasada, integridade dos ledgers, contratos/hashes, autenticação e limites da API, expiração de release, catálogo dos modelos, política causal de compra, notícias, fila dupla e simulação de anotação e um stress de 1.500 observações com mudanças de regime. O smoke API-only local passou com 500/500 respostas, 267 req/s, p95 de 91,2 ms e p99 de 142,1 ms; esses números não substituem medição em cloud.

## Estabilidade, complexidade e limitações

- Entradas devem ser escaladas para `[0,1]` a partir do treino. O recorte não é silencioso por padrão.
- Inversões usam `pinv` como contingência, matrizes são simetrizadas e denominadores têm piso numérico.
- Predição por regra custa `O(Dm)`. Atualização coerente custa `O(D²)` e inserção/reconstrução pode chegar a `O(D³)`, onde `D` é o limite do dicionário.
- A fusão de consequentes, a substituição com dicionário cheio e a atualização de amostras coerentes exigiram políticas de engenharia, pois não são completamente especificadas nas fontes.
- A equação literal do centro pode congelar componentes iniciados em zero; a alternativa documentada `center_update="compatibility"` existe para análise de sensibilidade.
- A fonte usa a notação de erro normalizado, mas não define uma normalização online separada de forma inequívoca. `none` é fiel quando o alvo já foi escalado; os modos running são extensões.
- A reprodução da Tabela 5 não foi certificada; o artefato operacional usa apenas a série S10 local versionada e um protocolo temporal novo.
- O ARIMA está aprovado apenas para rollout controlado: o ganho do holdout é prático, porém não significativo a 5%. O VS continua em shadow mode e sua saturação estrutural exige nova pesquisa antes de promoção.
- Recuperação de `beta`, esquecimento, utilidade recente, correção residual amortecida e atributos exógenos são extensões de engenharia, não partes da fórmula VS original. Elas ficam desligadas por padrão ou isoladas no experimento challenger.
- O churn do KRLS permanece material (144 substituições no challenger operacional); aumentar o dicionário reduziu churn, mas piorou a validação, portanto capacidade não deve ser ampliada sem nova evidência.

O notebook [notebooks/reproduction_experiment.ipynb](notebooks/reproduction_experiment.ipynb) organiza a reprodução e deixa a célula ANP condicionada ao CSV local.

## Pipeline legado do repositório

Os scripts `01_download.py` a `04_producao.py` e o pacote `vsepl_krls` pertencem à investigação anterior. Foram preservados para rastreabilidade, mas a operação nova usa os scripts `05` a `07` e o bundle `vs_epl_krls.production`.
