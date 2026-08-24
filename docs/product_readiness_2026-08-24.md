# Auditoria de prontidão profissional — 24/08/2026

## Veredito executivo

O S10 Intelligence está pronto para **demonstração técnica a investidores e piloto controlado com cliente**, não para compra autônoma em escala enterprise. O produto é API-only e reúne previsão, incerteza, impacto financeiro, release imutável, proveniência da ANP, API protegida, observabilidade, auditoria encadeada e evidência reproduzível. A limitação dominante deixou de ser engenharia básica e passou a ser validação comercial prospectiva com dados reais do comprador.

## Evidência fechada nesta auditoria

| Área | Resultado | Gate |
|---|---:|---:|
| testes | 215 aprovados; 2 opcionais ignorados | passou |
| cobertura | 90,05% de 4.341 statements | passou (≥90%) |
| lint / tipos / compile | Ruff, mypy e compileall sem erro | passou |
| dependências | `pip check` íntegro; 0 vulnerabilidades conhecidas no lock e ambiente local | passou |
| carga local ASGI | 500/500, 267 req/s, p95 91,2 ms, p99 142,1 ms | passou |
| release | SHA-256 e round-trip verificados; previsão vencida é bloqueada | passou |
| container | Dockerfile e Compose endurecidos | não executado: Docker ausente na máquina |

O teste de carga é in-process nesta máquina e serve como regressão de software, não como SLO cloud. Os dois skips são benchmarks GBM/LSTM opcionais, excluídos do runtime de produção para reduzir superfície de ataque e peso operacional.

## Desempenho do modelo e decisão

- ARIMA primário: RMSE 0,08145 e MAE 0,02706 em holdout temporal de 104 semanas.
- Persistência: RMSE 0,09563; redução prática do ARIMA de 14,8%.
- Direção correta do ARIMA: 59,2%; teste Diebold–Mariano `p=0,1338`, portanto o ganho não é conclusivo a 5%.
- VS-ePL-KRLS: RMSE 0,09382, ganho de 1,90% sobre persistência e `p=0,0395`; não atingiu o gate pré-fixado de 2% e segue challenger.
- Intervalo P10–P90 nominal de 80%: cobertura de 92,3%, conservadora.
- Shadow prospectivo: 1/26 observações mínimas; promoção automática proibida.

## Valor econômico medido

No replay causal pré-fixado para 200 mil litros/mês, antecipando 25% de uma semana quando a alta prevista excede R$ 0,01/L:

- economia histórica líquida: R$ 16.961,54 em 104 semanas;
- valor anualizado: R$ 8.563,11;
- intervalo bootstrap de 90% anual: R$ 116,50 a R$ 23.653,40;
- 9 gatilhos, com precisão de 66,7%;
- 50,34% da economia veio do maior evento; sem ele, R$ 8.423,08 no período.

Isso é replay de política, não promessa de economia. Frete, preço contratual, estoque e capital do cliente ainda não estão modelados.

## Correções e capacidades entregues

1. Ingestão estrita da planilha semanal oficial da ANP com produto, unidade, semana, postos, preço, URL e hash.
2. Release imutável com manifesto, parent hash, fingerprint e ledgers tamper-evident.
3. API somente leitura com chave obrigatória em produção, rate limit, limite de corpo, hosts confiáveis, request ID, headers de segurança, health/readiness e métricas.
4. Bloqueio 503 de forecast vencido e cache imutável do release para previsibilidade de latência.
5. Contrato API-only: a raiz e os endpoints de forecast, modelos, evidências e cenários retornam dados, sem frontend customizado.
6. Replay causal de decisão com bootstrap e análise de concentração.
7. CI com lint, tipos, auditoria de dependências, compile, testes e cobertura.
8. SBOM CycloneDX, lock de produção, container sem root/read-only e documentação de arquitetura, segurança, SLO e runbook.

Os dois históricos permanecem verificáveis sem reescrita: o ledger de produção usa o formato canônico novo com gênese `null` (3 registros; head `0a454392…`), enquanto o experimento shadow preserva seu contrato congelado anterior com gênese de 64 zeros (4 registros; head `a1e5f4ee…`) e verificador próprio. Essa separação evita invalidar evidência prospectiva já registrada.

## Bloqueadores para enterprise, em ordem

1. Executar piloto shadow de 12 semanas com cotações, estoque, decisões e custos reais de 2–3 clientes.
2. Implantar em cloud privada e comprovar SLO, alertas, backup, recovery e rollback sob falhas.
3. Substituir chave compartilhada por identidade organizacional, RBAC, secrets manager e audit log central.
4. Modelar preço regional/fornecedor, capacidade, custo financeiro, lead time e lote mínimo.
5. Fazer pentest e revisão matemática independente; assinar imagem e release no CI.
6. Acumular pelo menos 26 resultados prospectivos antes de qualquer promoção do challenger.

## Regra de narrativa

Apresentar sempre resultado, intervalo e limite juntos. O posicionamento correto é: **software e governança prontos para piloto; valor econômico promissor, ainda a validar nas condições reais do cliente; nenhuma decisão de compra é executada automaticamente**.
