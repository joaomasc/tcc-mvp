# Changelog

## Não lançado

- janela de validação e holdout congelada por data em vez de deslocamento a
  partir do fim da série: `pinned_validation_folds()` resolve o corte pelas
  semanas-alvo 2024-08-18 a 2026-08-09, falha alto se elas não existirem e trata
  dados posteriores como cauda prospectiva;
- scripts 05, 08, 19 e 22 migrados para a janela congelada; o 08 aborta se os
  índices herdados do manifesto de produção divergirem das datas;
- regressão em `tests/test_pinned_windows.py` cobrindo crescimento do painel,
  buracos na série, datas ausentes e fora de ordem;
- ledger prospectivo do modelo de paridade: `23_s10_parity_production.py` grava
  cada previsão em `parity_ledger.jsonl` encadeado por SHA-256 e liquida a
  semana anterior contra o realizado, com erro do modelo, erro da persistência e
  cobertura do intervalo;
- previsão de 2026-08-23 emitida pelo modelo de paridade: R$ 6,9121/L, gatilho de
  antecipação acionado;
- caminhos gravados na evidência de paridade agora são relativos ao repositório,
  não absolutos da máquina que treinou;
- CI: removida do passo de mypy a referência a `src/vs_epl_krls/dashboard.py`, um
  arquivo que nunca existiu no repositório e que fazia o passo falhar sempre;
- CHANGELOG 0.2.0 corrigido: não há dashboard executivo, o produto é API-only;
- `ruff` fixado em `>=0.12,<0.13`: a partir da 0.13 o conjunto de regras padrão
  reprova centenas de linhas pré-existentes e derrubava a CI no passo de lint;
- **gates decidíveis** (`vs_epl_krls.gates`): MAE, decomposição por regime,
  *interval score* de Winkler, bootstrap em blocos móveis pareado, Diebold-Mariano
  com correção Harvey-Leybourne-Newbold e economia líquida como KPI primário;
  `24_s10_gate_review.py` aplica sobre a evidência publicada e fecha três decisões
  que estavam travadas — paridade não promove, VS-ePL-KRLS não promove, intervalo
  não estava calibrado;
- **intervalo conformal adaptativo** (`vs_epl_krls.calibration`): Gibbs e Candès
  sobre resíduo normalizado; ativo na previsão do modelo de paridade, cobertura de
  78,8% para nominal de 80% com banda 19,4% mais estreita e Winkler melhor. O
  bundle de produção continua com o intervalo antigo: trocá-lo exige release nova;
- **camada de decisão** (`vs_epl_krls.decision`) e endpoints `POST /v1/decision` e
  `GET /v1/governance`: recomendação acionável com volume, economia esperada,
  exposição, confiança e divergência entre modelos explícita;
- **verificação de runtime da release**: divergência de versão de numpy, pandas,
  scikit-learn, statsmodels ou joblib em relação à que gerou o artefato marca o
  status como `degraded` com motivo explícito;
- **pressão de repasse** (`vs_epl_krls.pressure`) e `25_s10_pressure_experiment.py`:
  indicador antecedente disponível em tempo real, avaliado apenas em
  desenvolvimento; mecanismo confirmado, magnitude não estabelecida, nada promovido;
- `ProcurementBacktest` expõe a série semanal de economia líquida, necessária para
  reamostragem em blocos;
- **modelo estadual** (`vs_epl_krls.regional`) e `26_s10_rs_regional.py`: ingestão
  da série semanal da ANP por unidade da federação com proveniência e SHA-256,
  preço de produtor casado com a região do estado, e decomposição
  `estado = nacional + spread` com correção de erro sobre o spread. Avaliado em
  desenvolvimento para o RS; o holdout estadual permanece fechado;
- **RS em produção** (`27_s10_rs_production.py`): artefato versificado por SHA-256,
  intervalo conformal calibrado, ledger prospectivo próprio e relatório de base;
- **decisão e base estaduais na API**: `POST /v1/decision` aceita `uf` e
  `POST /v1/basis` devolve o custo de orçar pela média nacional, escalado pelo
  volume do cliente. A confiança de uma decisão estadual é limitada por código a
  `media` enquanto a evidência for `development_only`;
- mecânica de ledger extraída para `vs_epl_krls.audit` (`record_forecast`,
  `settle_pending_forecast`), agora compartilhada entre paridade e estadual;
- **dez estados servidos com um download** (`28_s10_multi_state.py`): a planilha da
  ANP é baixada e lida uma vez, e a previsão nacional é calculada uma vez para
  todos. `pool_reversion()` implementa o encolhimento de DerSimonian-Laird e
  `SpreadForecaster(weight_by_stations=True)` pondera cada semana pelo tamanho da
  amostra pesquisada;
- **intervalo do bundle de produção aprende o nível** (contrato `1.2.0`, aceitando
  `1.1.0` sem mudança de comportamento): `warm_start_interval_alpha()` faz a
  release nascer calibrada em vez de levar dezenas de semanas para se corrigir;
- **alertas dos ledgers** (`vs_epl_krls.monitoring`, `29_s10_ledger_review.py`):
  liquidação atrasada, cobertura fora da faixa, pior que a persistência e contagem
  atingida. Expostos em `GET /v1/governance` e com código de saída para
  agendador;
- **VS-ePL-KRLS avaliado no spread estadual** (`30_s10_vs_on_spread.py`), com
  diagnóstico de previsibilidade por horizonte. Hipótese fechada em h=1;
- correção: `SpreadForecaster.walk_forward` descartava os parâmetros de pooling ao
  construir o modelo interno, o que tornava o encolhimento invisível na avaliação.

## 0.2.0 — 2026-08-23

- camada de produto S10 com verificação de integridade e bloqueio de forecast vencido;
- API FastAPI read-only, autenticação de produção, limites, headers e métricas;
- snapshot de evidência para investidores (JSON; o produto é API-only e não tem frontend);
- parser estrito da planilha semanal oficial ANP;
- release imutável e ledger de produção encadeado por SHA-256;
- primeira observação prospectiva incorporada à produção e ao shadow;
- replay causal da política de antecipação para 200 mil L/mês;
- container hardening, threat model, SLOs, arquitetura e auditoria de prontidão.

