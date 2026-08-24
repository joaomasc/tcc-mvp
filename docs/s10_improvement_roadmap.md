# Melhorias executadas e roadmap profissional — Diesel B S10

> Este documento registra **o que já foi feito e por quê**. O que ainda não existe — avanços
> de produto, de modelo e endurecimento do que está pronto — está em
> [roadmap_produto.md](roadmap_produto.md).

## Decisão atual

O serviço de previsão deve manter **ARIMA como primário**, persistência como fallback final e VS-ePL-KRLS como challenger. O bundle 1.1 está adequado para rollout controlado, mas o VS e o novo híbrido ainda não possuem evidência para promoção. O holdout final já foi aberto e não pode ser reutilizado para escolher a próxima versão.

> **Atualização de 24/08/2026, terceira rodada:** essa decisão deixou de ser cautela e passou a ser resultado medido. Os gates decidíveis ([`gates.py`](../src/vs_epl_krls/gates.py), [relatório](../reports/vs_epl_krls/s10_gates/report.md)) fecham as três perguntas que estavam travadas: paridade **não** promove (perde no MAE e piora 44% nas semanas paradas, mesmo passando nos três gates econômicos), VS-ePL-KRLS **não** promove (falha nos seis gates), e o intervalo P10-P90 **não estava calibrado** (cobria 89,4% para um nominal de 80%). Este último foi corrigido em produção.

> Atualização de 2026-08-24: o experimento de repasse causal ([relatório](../reports/vs_epl_krls/s10_passthrough/report.md)) fechou o espaço de busca endógeno com evidência e explica por que os challengers não passam nos gates. Leia a seção "Teto de informação" antes de abrir qualquer nova frente de modelagem.
>
> Atualização seguinte, mesma data: com dados causais novos, o **modelo de paridade de diesel superou o ARIMA no holdout** ([relatório](../reports/vs_epl_krls/s10_parity/report.md)) — RMSE 0,080807 contra 0,081463, acurácia direcional 71,8% contra 59,2% e economia R$ 19.385 contra R$ 16.962. Ele é o candidato a primário. A seção "Teto trancado por publicação" abaixo registra o ganho maior que continua fora de alcance.

## Correção de protocolo — janela congelada por data

Até 24/08/2026 todo corte temporal do projeto era ancorado no fim da série:
`development_end = n - holdout_size`, em [`selection.py`](../src/vs_epl_krls/selection.py)
e replicado nos scripts 19 e 22. Isso significa que **os três folds e o holdout
escorregavam uma posição a cada semana nova publicada pela ANP**.

Duas consequências, ambas verificadas ao reinstalar o projeto numa máquina nova:

1. **A evidência publicada deixava de ser reproduzível.** Com uma única semana a
   mais no painel (702 → 703), uma semana de evento cruzou a fronteira entre os
   folds 2 e 3. O RMSE da persistência foi de 0,0929 para 0,1190 no fold 2 e de
   0,0819 para 0,0298 no fold 3 — variação de 40% a 170% causada por um único
   ponto mudando de lado. É a tese do "tamanho amostral efetivo de ~3" desta
   seção se manifestando de forma operacional.
2. **O holdout se reabria sem aviso.** Reexecutar `22_s10_parity_selection.py`
   após dados novos não seria a terceira leitura do mesmo holdout: seria a
   leitura de um holdout *diferente*, com semanas que nunca estiveram nele. A
   proteção que o protocolo descrevia não existia na prática.

O corte agora é resolvido por data, não por deslocamento:
`pinned_validation_folds()` procura as semanas-alvo congeladas do holdout
(**2024-08-18 a 2026-08-09**, 104 semanas) e falha alto se elas não existirem
exatamente uma vez na série, se houver buraco dentro da janela ou se as datas não
estiverem ordenadas. Tudo que vier depois de 2026-08-09 é **cauda prospectiva**:
fica registrado no manifesto, e nunca entra em desenvolvimento ou holdout.

Scripts 05, 08, 19 e 22 usam a janela congelada. O 08 compara os índices herdados
do manifesto de produção com os índices resolvidos por data e aborta se
divergirem. `expanding_validation_folds()` continua no módulo, com a ressalva na
docstring, porque testes históricos dependem dela.

Verificação: com o painel de 703 semanas, os quatro scripts resolvem exatamente
as janelas publicadas — folds 442/494/546 e holdout 598..702 no painel de paridade,
folds 429/481/533 e holdout 585..689 no conjunto supervisionado — e os folds de
desenvolvimento reproduzem o CSV commitado com diferença máxima de 7,5·10⁻⁸ em
RMSE. Antes da correção, a mesma execução divergia em até 170%. A regressão está
em [`tests/test_pinned_windows.py`](../tests/test_pinned_windows.py).

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

### Contagem prospectiva do paridade

O holdout está gasto: daqui em diante só semanas futuras decidem. Até 24/08/2026
não havia como contá-las — `23_s10_parity_production.py` sobrescrevia
`latest_forecast.json` a cada execução, então a previsão da semana anterior
desaparecia antes de poder ser comparada com o realizado.

Agora cada execução grava a previsão em
[`parity_ledger.jsonl`](../reports/vs_epl_krls/s10_parity/parity_ledger.jsonl),
append-only e encadeado por SHA-256 pelo mesmo mecanismo do ledger de produção, e
liquida a previsão pendente assim que a semana-alvo dela aparece no painel —
registrando erro do modelo, erro da persistência, cobertura do intervalo e o hash
do registro de previsão que está sendo pontuado. A liquidação é idempotente: uma
semana nunca é contada duas vezes.

Estado: **0/26 semanas liquidadas**. O ledger começa na previsão de 2026-08-23; a
observação prospectiva de 2026-08-16 relatada em §4.2 do relatório é anterior ao
ledger e por isso não entra na contagem.

Primeira divergência direcional em tempo real, semana de 2026-08-23:

| modelo | previsão | direção | gatilho |
|---|---:|---|---|
| paridade | R$ 6,9121/L | alta de R$ 0,0221 | **antecipar** 11.538 L |
| ARIMA (produção) | R$ 6,8821/L | queda de R$ 0,0079 | não antecipar |

Preço de origem: R$ 6,89/L em 2026-08-16. Os dois modelos discordam do sinal, o
que torna esta semana informativa de verdade — e é exatamente o tipo de evidência
que nenhuma releitura do holdout produz.

## Modelo estadual — a mudança que resolve a fragilidade comercial

A maior fragilidade do projeto nunca foi estatística: era o alvo. O produto previa a média
nacional de revenda da ANP, que nenhum comprador paga. A ANP publica a mesma pesquisa por
estado, e passar a usá-la ([`regional.py`](../src/vs_epl_krls/regional.py),
[relatório](../reports/vs_epl_krls/s10_rs/report.md)) troca uma aproximação por um número
verdadeiro.

**Arquitetura escolhida por medição.** A variação semanal do RS correlaciona 0,939 com a
nacional — 88% da variância estadual é movimento do país — e o desvio da variação do spread
é 0,0264 contra 0,0769 do preço. Daí `estado = nacional + spread`, com correção de erro
sobre o spread em vez de modelar o estado direto.

| desenvolvimento, 156 semanas | MAE | direcional | economia | precisão |
|---|---:|---:|---:|---:|
| RS direto | 0,059437 | 65,2% | R$ 38.088 | 51,8% |
| **nacional + spread** | **0,057294** | **69,6%** | **R$ 46.292** | **60,0%** |

+21,5% de economia e +8,2 pontos de precisão de gatilho. O ganho de MAE não é decidível.
Terceira vez que o projeto encontra o mesmo padrão: **decide melhor do que prevê.**

**A âncora regional não ajudou.** O preço de produtor da região Sul é mensuravelmente
melhor que a mediana nacional como insumo (+0,4265 contra +0,3952 na defasagem de uma
semana), mas o *spread* de produtor explica o nível do spread de revenda (+0,25) e quase
nada da variação semanal (+0,06). Peso estimado no modelo: −0,0102. Registrado como
hipótese fechada.

**O modelo estadual é pior que o nacional, e isso é estrutural.** MAE 0,0573 contra 0,0505,
direcional 69,6% contra 74,3%. São 262 postos pesquisados contra 3.173. Não há modelagem
que conserte tamanho de amostra; quem vender o modelo estadual como "mais preciso" estará
errado.

**Onde o valor está, medido.** Para 200 mil L/mês no RS, o erro de orçamento por usar a
série nacional é de R$ 336.000/ano contra R$ 15.631/ano de economia da política de
antecipação — uma razão de **21,5×**. O produto estadual não se vende pela previsão; vende-se
por entregar a série que o cliente efetivamente enfrenta.

**Posição corrente, com a ressalva de amostra.** O spread está no percentil 0,6% de 702
semanas (z = −2,96). Das 7 semanas já vistas nesse nível, 5 são o episódio corrente: sobram
**2 precedentes**. Em faixas com mais episódios independentes a direção da reversão se
sustenta (78% a 89% de altas em 3 a 6 episódios), mas a magnitude no extremo atual não está
estabelecida e não deve ser apresentada como previsão.

**Custo marginal de outro estado: zero.** `UF_REGION` cobre as 27 unidades da federação e
o script aceita `--uf`. O trabalho de RS é o trabalho de qualquer estado.

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

## Mudança de gates — implementada

O gate antigo (ganho de 2% no RMSE, DM `p < 0,05`) não era decidível nesta série. A substituição recomendada está implementada em [`gates.py`](../src/vs_epl_krls/gates.py) e aplicada em [`24_s10_gate_review.py`](../scripts/24_s10_gate_review.py):

| antes | agora | por quê |
|---|---|---|
| RMSE | **MAE** | o erro quadrático tem cauda que dá tamanho amostral efetivo de ~3 |
| DM assintótico normal | **bootstrap em blocos** pareado; DM com correção Harvey-Leybourne-Newbold e referência `t(T-1)` quando usado | a média da diferença de perda não é normal em 104 pontos dependentes |
| métrica agregada | **decomposição por regime** (parada/evento) | em dois terços das semanas nada acontece e a persistência ganha de todos |
| cobertura do intervalo | ***interval score* de Winkler** | cobertura sozinha premia quem abre a banda |
| ganho de RMSE como KPI | **economia líquida com IC90 por bootstrap** | é a moeda em que o produto é defendido |
| — | **concentração**: fração da economia vinda do maior evento | separa política de aposta num episódio |

Todos os limiares são argumentos da função: nenhuma política fica escondida em número mágico.

Resultado da primeira aplicação, sobre evidência já publicada e sem nova leitura do holdout:

| pergunta | veredito | gates que falharam |
|---|---|---|
| paridade substitui ARIMA? | não promover | `mae_melhor_que_incumbente`, `sem_regressao_em_semana_parada` (+43,95%) |
| VS-ePL-KRLS promove? | não promover | todos os seis |

O achado mais útil não aparecia no RMSE: a paridade **decide melhor do que prevê**. Ganha em direção e economia, perde onde o preço não se move — o que explica mecanicamente os 26 gatilhos com 65,4% de precisão contra 8 com 75%.

Achado de processo a corrigir: `05_s10_model_selection.py:203` constrói apenas os conjuntos `price`, `lags` e `dynamics`. **O campeão de produção foi selecionado sem jamais ver Brent ou câmbio.**

## Intervalo: de conservador para calibrado

Os dois intervalos do projeto usavam quantis de resíduo com nível nominal fixo e cobriam demais: 89,4% no modelo de paridade e 92,3% no bundle de produção, ambos para um nominal de 80%. Banda larga demais não é segurança grátis: ela desloca o cenário P90 e distorce o custo aparente de antecipar.

[`calibration.py`](../src/vs_epl_krls/calibration.py) implementa inferência conformal adaptativa (Gibbs e Candès, 2021) sobre resíduo **normalizado** — a escala condicional continua do modelo, o nível de miscobertura passa a ser aprendido online. Medido em 156 semanas de calibração causal e já ativo na previsão operacional da paridade:

| intervalo | cobertura (nominal 80%) | largura média | Winkler |
|---|---:|---:|---:|
| quantil fixo | 90,4% | 0,0858 | 0,1567 |
| conformal adaptativo | **78,8%** | **0,0691** | **0,1525** |

Banda 19,4% mais estreita, cobertura no alvo e pontuação própria melhor. Desvio deliberado em relação ao artigo: `alpha` é limitado em vez de permitir intervalo infinito, e cada passo em que o limite foi atingido fica registrado.

**Escopo do que já mudou:** só a previsão do modelo de paridade. O intervalo do bundle de produção está dentro do artefato congelado; aplicá-lo lá exige uma release nova com hash, ledger e evidência próprios, e é a próxima ação de release recomendada.

## Pressão de repasse — fronteira atacada, hipótese não promovida

A pesquisa confirmou o que o roadmap supunha: os anúncios de reajuste da Petrobras existem, são públicos e trazem data e magnitude em R$/L (ex.: 31/01/2025, +R$ 0,22/L no diesel A), mas saem como texto de assessoria, sem série baixável.

[`pressure.py`](../src/vs_epl_krls/pressure.py) tenta o mecanismo em vez do anúncio: a distância entre o último preço de produtor publicado e a paridade de importação corrente, disponível em tempo real.

O mecanismo aparece com força, sobre 491 semanas de desenvolvimento:

| quintil de pressão | variação média seguinte | taxa de semana de evento |
|---|---:|---:|
| menor pressão (refinaria barata vs paridade) | **R$ +0,0461/L** | **55,6%** |
| maior pressão | R$ −0,0009/L | 6,1% |
| base | — | 34,2% |

E mesmo assim **nada foi promovido**. Nenhuma especificação com pressão melhora o MAE de forma decidível; o ganho aparece só na economia (R$ 49.212 contra R$ 45.162). E a auditoria do próprio achado mostra por que não dá para confiar na magnitude: **41% da correlação com o resíduo do modelo congelado desaparece ao remover três semanas**, em posto sobra Spearman −0,16, e o lado alto do portão tem 9 das 156 semanas dos folds. O mesmo tamanho amostral efetivo minúsculo que invalidou os gates antigos invalida a leitura otimista deste resultado.

A especificação fica pré-registrada. Só semanas futuras, pelo ledger prospectivo, podem decidir.

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

1. **Em andamento — 1/26 no shadow VS, 0/26 no paridade:** acumular no mínimo 26 semanas futuras sem ajustar o challenger; 52 semanas são preferíveis. A realização oficial de 2026-08-16 foi registrada com proveniência ANP; faltam 25 semanas para o gate mínimo do shadow. O paridade passou a acumular a partir da previsão de 2026-08-23, no ledger próprio.
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
