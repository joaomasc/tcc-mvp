# Runbook de produção — Diesel B S10 nacional, horizonte de uma semana

## Status de aprovação

O bundle `artifacts/s10_production.joblib`, contrato **1.1.0**, está apto para **rollout controlado**. O modelo primário é ARIMA; o VS-ePL-KRLS roda como challenger em shadow mode e não pode substituir o primário automaticamente. O escopo não inclui S500, diesel genérico, estados, municípios ou preços de postos individuais.

O holdout final contém 104 semanas e não foi usado na seleção. O ARIMA obteve RMSE 0,08145 contra 0,09563 da persistência, mas o teste de Diebold–Mariano teve `p=0,1338`. Assim, o ganho é operacionalmente relevante, mas ainda não significativo a 5%; toda decisão deve conservar fallback e telemetria.

## Contrato de entrada

Cada atualização aceita exatamente:

- `date`: data posterior à última observação, normalmente sete dias depois;
- `price`: preço médio nacional de revenda do Diesel B S10, finito e positivo;
- fonte institucional ANP e mesma regra de agregação semanal usada no treino.

Rejeitar antes do modelo: datas duplicadas/retroativas, preço ausente, infinito, zero ou negativo, produto diferente de S10, unidade diferente de R$/L, geografia diferente de Brasil e alteração não versionada da agregação. Uma cadência fora de `7 ± 2` dias gera warning de saúde. Uma variação observada acima do limite histórico robusto é recusada; `--allow-anomalous-change` só pode ser usado depois de conferir fonte, unidade e publicação da ANP.

## Construção reproduzível

```powershell
.venv\Scripts\python.exe scripts\05_s10_model_selection.py --horizon 1
.venv\Scripts\python.exe scripts\06_train_s10_production.py
.venv\Scripts\python.exe scripts\07_s10_predict.py --output reports\vs_epl_krls\s10_production\latest_forecast.json
```

Antes de publicar, conferir:

1. `production_candidate_passed` e o primário em `selection_manifest_h1.json`;
2. `roundtrip_exact=true` no `forecast.json`;
3. SHA-256 do artefato e fingerprint dos dados;
4. `pytest` completo, cobertura mínima de 90% e `compileall` sem falha;
5. previsão finita, positiva e contida em P10–P90;
6. ausência de fallback durante o teste de smoke.
7. `artifact_version=1.1.0`; versões anteriores são incompatíveis e devem permanecer apenas no arquivo histórico.

O holdout não pode ser reutilizado para escolher parâmetros. Depois que uma nova seleção for aprovada, avance a janela temporal e mantenha outra janela final intocada.

## Operação semanal

Primeiro gere a previsão atual em modo somente leitura:

```powershell
.venv\Scripts\python.exe scripts\07_s10_predict.py
```

Quando a ANP publicar o valor observado, preserve o artefato anterior e gere um novo arquivo canário:

```powershell
New-Item -ItemType Directory -Force artifacts\archive
Copy-Item artifacts\s10_production.joblib artifacts\archive\s10_production_PREVIOUS.joblib
.venv\Scripts\python.exe scripts\07_s10_predict.py `
  --update-date 2026-08-16 `
  --update-price 6.90 `
  --output-artifact artifacts\s10_production_candidate.joblib `
  --output reports\vs_epl_krls\s10_production\latest_forecast.json
```

Valide o JSON, a fonte e `health()`. Promova o canário por uma operação atômica da plataforma somente após aprovação; nunca use um preço ilustrativo como o do comando acima em produção.

Na mesma janela, reemita a previsão do challenger de paridade:

```powershell
.venv\Scripts\python.exe scripts\21_s10_ingest_causal.py
.venv\Scripts\python.exe scripts\23_s10_parity_production.py
```

O script faz três coisas na ordem certa e é idempotente: liquida no `parity_ledger.jsonl` a previsão da semana anterior contra o valor oficial que acabou de chegar, recalibra o nível do intervalo pelas últimas 156 semanas de walk-forward causal, e registra a nova previsão. Reexecutar com saída idêntica não acrescenta registro; reexecutar com artefato diferente registra uma **revisão** encadeada, nunca uma sobrescrita. A contagem prospectiva impressa no fim (`n/26`) é a única que vale para decidir promoção.

Para cada estado servido, na mesma janela:

```powershell
.venv\Scripts\python.exe scripts\26_s10_rs_regional.py --uf RS
.venv\Scripts\python.exe scripts\27_s10_rs_production.py --uf RS
```

O `27` liquida a semana anterior no ledger estadual, recalibra o nível do intervalo e registra a nova previsão, com a mesma idempotência e o mesmo encadeamento de revisões do modelo de paridade. Ele **recusa emitir** se a última semana observada do estado não for a origem da previsão nacional vigente — evitando servir números de períodos diferentes lado a lado.

Suba o serviço declarando os estados: `python scripts\15_s10_service.py --state RS`.

## Verificação de runtime

Antes de servir, confira que o ambiente é o do `requirements-service.lock`. O SHA-256 garante os bytes da release, não o runtime que os interpreta: numpy, pandas, scikit-learn, statsmodels e joblib mudam resultado numérico entre versões. `GET /v1/health/ready` devolve `runtime_verified` e lista cada divergência em `reasons`; status `degraded` com `runtime_mismatch:*` significa que a previsão servida pode não ser a que foi avaliada.

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-service.lock
```

## Telemetria e alertas

Registrar por previsão: timestamp, versão/hash, fingerprint, última data/preço, ponto/P10/P90, todos os componentes, fallback e motivo, latência, erro quando o alvo chegar, cobertura móvel, regras, beta, maior dicionário, clipping e cadência.

Alertas sugeridos:

| Sinal | Warning | Ação crítica |
|---|---:|---:|
| latência p95 | > 20 ms | > 100 ms ou timeout |
| feature clipping | > 5% por 4 semanas | > 25% em uma previsão |
| cobertura P10–P90 móvel (mínimo 20; alvo 26 semanas) | < 70% ou > 95% | < 60% |
| RMSE / persistência móvel (26 semanas) | > 1,00 | > 1,10 |
| erro absoluto | acima do P90 calibrado | 3 vezes o P90 |
| cadência | fora de 5–9 dias | data duplicada/retroativa |
| capacidade VS | ≥ 90% | 100% por 8 semanas |
| churn do dicionário | ≥ 40% | aumento sustentado com regressão de erro |

No artefato atual, o challenger ocupa 13/20 regras e 20/20 kernels, acumulou 144 substituições (20,9% das atualizações) e `beta` permanece no piso de `1e-4`. A pressão do dicionário, churn e piso de beta são warnings conhecidos. Como o VS não é primário, eles não interrompem o serviço, mas bloqueiam sua promoção.

Recuperação de beta, forgetting, utilidade recente e dicionários maiores já foram avaliados apenas nos folds de desenvolvimento e não superaram o VS direto congelado. O híbrido residual conservador melhorou marginalmente o ARIMA nos três folds e fica em shadow research. Nenhum desses resultados autoriza consultar novamente o holdout ou trocar o primário; a próxima evidência válida deve vir de observações futuras.

## Fallback e rollback

O runtime usa persistência quando o primário ARIMA não é finito ou prevê uma mudança fora do limite robusto. Se um challenger vier a ser primário, o ARIMA seguro é o primeiro fallback e a persistência é o último.

Rollback imediato quando houver artefato ilegível, schema incompatível, hash inesperado, previsão não finita, regressão de RMSE móvel acima de 10%, falhas repetidas de atualização ou origem de dados incorreta. Restaure o artefato anterior arquivado e mantenha persistência enquanto o incidente é investigado. Não tente reparar manualmente matrizes KRLS serializadas.

## Política de retreino e promoção

Retreinar trimestralmente ou antecipadamente quando houver drift, dois fallbacks em 13 semanas, cobertura crítica, mudança de metodologia ANP ou regressão sustentada contra persistência. Para promover qualquer modelo:

- seleção exclusivamente em folds temporais expansivos;
- pelo menos 100 previsões no holdout final;
- previsões finitas e limites de memória/latência respeitados;
- RMSE no mínimo 2% melhor que persistência e desempenho consistente em todos os folds;
- teste de Diebold–Mariano com `p<0,05` como gate para promover o VS;
- churn KRLS abaixo de 40% e ausência de saturação/incidentes sustentados;
- revisão humana do data lineage, gráficos de resíduos e incidentes.

O modelo primário pode permanecer ARIMA enquanto o VS não satisfizer esses critérios. A arquitetura permite melhorar o challenger sem arriscar a continuidade da previsão.

## Operação do shadow prospectivo

O híbrido residual foi congelado separadamente em `artifacts/s10_shadow_hybrid_v1.joblib`. Ele nunca substitui nem atualiza `s10_production.joblib`. Para consultar o forecast pendente:

```powershell
.venv\Scripts\python.exe scripts\09_s10_shadow.py
```

Quando o valor oficial referente exatamente à `target_date` chegar, preserve o artefato anterior e escreva uma nova versão:

```powershell
.venv\Scripts\python.exe scripts\09_s10_shadow.py `
  --update-date AAAA-MM-DD `
  --update-price VALOR_OFICIAL `
  --output-artifact artifacts\s10_shadow_hybrid_SEMANA.joblib
```

O comando recusa data diferente da previsão pendente, preço inválido, alteração in-place, hash/fingerprint divergente ou ledger adulterado. Primeiro registra o resultado de ARIMA, híbrido e persistência; depois revela `actual - ARIMA` ao VS, emite a previsão seguinte, salva novo artefato e acrescenta `outcome`/`forecast` à cadeia.

Não reutilizar o comando `--freeze`: os alvos existentes são imutáveis e a CLI recusa sobrescrita. O gate exige no mínimo 26 realizações futuras, prefere 52, mede ganho mínimo de 2%, pior janela de 13 semanas e significância contra ARIMA. Nenhum resultado aciona promoção automática; apenas libera revisão humana.

## Recuperação e retenção

Reter dados de entrada imutáveis, manifest, ranking, predições do holdout, resíduos de calibração, model card, ambiente/dependências, artefato e SHA-256 de cada release. Uma restauração só é válida se `S10ProductionForecaster.load()` aceitar a versão e a previsão repetida for idêntica ao registro original.
