# S10 Intelligence — brief para investidores

## A tese

Empresas que compram diesel não precisam de “mais um modelo”; precisam saber quanto está em risco, qual evidência sustenta o sinal e quando não confiar nele. O S10 Intelligence transforma a série semanal oficial da ANP em previsão de uma semana, faixa de incerteza e replay auditável de políticas de antecipação de compra.

## O produto hoje

- API JSON para Diesel B S10 nacional, pronta para integração com sistemas do cliente;
- release imutável com fonte, hash, fingerprint e ledger verificável;
- ARIMA primário, persistência como fallback e VS-ePL-KRLS evolutivo em shadow;
- previsão bloqueada automaticamente quando vence;
- cenário instantâneo: em 200 mil L/mês, cada R$ 0,01/L representa R$ 2 mil;
- notícias coletadas com proveniência continuam em pesquisa porque ainda não melhoraram o forecast.

## Evidência

No holdout final de 104 semanas, o ARIMA obteve RMSE 0,08145 contra 0,09563 da persistência, redução de 14,8%. O teste Diebold–Mariano teve p=0,1338, portanto o ganho não é conclusivo a 5% e não deve ser vendido como certeza.

Uma política pré-fixada — antecipar 25% de uma semana quando a alta prevista supera R$ 0,01/L — produziu R$ 16.962 em dois anos para uma empresa de 200 mil L/mês, ou R$ 8.563 anualizados. Foram nove antecipações, 66,7% seguidas por alta. Metade da economia veio do maior choque; sem ele restam R$ 8.423 no período. O cálculo não inclui condições de fornecedor, capacidade física ou custo financeiro.

A primeira observação prospectiva oficial foi positiva para o primário: previsão R$ 6,898/L, realizado R$ 6,89/L, erro absoluto R$ 0,0081/L. O challenger híbrido teve R$ 0,0091/L e continua coletando evidência (1/26).

## Diferencial defensável

O diferencial não é uma arquitetura isolada. É o conjunto de dados governados, protocolo temporal sem vazamento, políticas de decisão reexecutáveis, releases rastreáveis, challenger online e disciplina de não promover hipóteses que falham. Isso reduz risco de modelo e aumenta confiança comercial.

## Piloto comercial sugerido

Selecionar 2–3 empresas com histórico de cotações, consumo, estoque e regras de compra. Durante 12 semanas, rodar apenas em shadow: registrar o preço realmente disponível ao comprador, a decisão humana, custos de armazenamento e o contrafactual definido antes do período. KPI primário: economia líquida realizável por litro; secundários: cobertura, adoção, overrides e tempo poupado. O modelo científico continua acumulando pelo menos 26 semanas prospectivas.

## O que ainda falta para escala enterprise

- dados de fornecedor/região e restrições reais de estoque;
- autenticação por usuário/empresa, RBAC e integração com ERP/procurement;
- implantação cloud com SLO medido, alertas, registry, assinatura de imagem e pentest;
- 25 resultados prospectivos adicionais para o gate mínimo do challenger;
- validação independente da implementação matemática e da política econômica.

Posicionamento correto para investidores: **produto pronto para demonstração e piloto controlado; ainda não pronto para decisões autônomas de compra em escala enterprise**.
