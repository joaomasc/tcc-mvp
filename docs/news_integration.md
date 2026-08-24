# Integração DieselNews → previsão semanal S10

## Decisão atual

O sinal de notícias está integrado como **challenger de pesquisa**, não como entrada do modelo operacional. O backtest não encontrou ganho de RMSE consistente e, por isso, não alterou o ARIMA primário, o bundle `s10_production.joblib` nem o shadow `hybrid_dynamics_conservative`.

## Linhagem operacional

| Artefato | SHA-256 | Registros |
|---|---|---:|
| Catálogo governado de fontes | `3ca35163bdde3229cc8c5cab8f23bb57e86972a8a07f806139140ce0fe076c3c` | 4 ativas, 1 bloqueada |
| Evidência hash-only | `e4d76cb5878d84b54c4d769c98272a02547c028d60809a71fb16b264a380b2a1` | 20 |
| Proveniência HTTP | `a1f0307f93031a69a91b922ba51a17d62a23f20b720e9303700032d5940632d7` | 296 |
| Notícias v2 | `0ad4747dfe71d570982eb0d2e242dc6ee533d4f009403977485b144baa1aff18` | 5.752 |
| Sinal semanal v3 | `523a8d502025fc72ea6b87154f114eeeb22735fd2580645f3a4ad562b3c120c9` | 2.089 |

O contato fornecido pelo operador foi enviado somente no `User-Agent` durante as requisições. Ele não foi persistido no catálogo, nos manifestos, nos relatórios ou no corpus.

As fontes operacionais são ANP, IBGE, MME e Fazenda. Petrobras continua bloqueada. O sitemap IBGE respondeu 403, mas a listagem pública auditada permitiu um backfill paginado de 1.926 registros. A distribuição completa foi ANP 426, IBGE 1.926, MME 3.347 e Fazenda 53.

## Contrato causal

`load_weekly_news_features()` aceita o diretório versionado `weekly-signal/v3` ou um snapshot explícito. Antes de retornar qualquer variável, ele verifica:

- ponteiro `latest.json`, caminho canônico e checksum;
- manifesto v3 e endereço por conteúdo;
- SHA-256 de `signals.jsonl`;
- campos exatos, JSON sem chaves duplicadas, NaN ou Infinity;
- contagens, cobertura de fontes e mapas de direção/categoria;
- calendário ANP aos domingos e horizonte exato;
- unicidade de cada par origem/alvo.

`augment_supervised_with_news()` exige uma linha para toda origem supervisionada e preserva alvos, datas e folds. A agregação usa somente notícias com `first_available_at <= forecast_at`.

## Backtest

Comando:

```bash
python scripts/10_s10_news_backtest.py \
  --news-signals CAMINHO/weekly-signal/v3 \
  --output-dir reports/vs_epl_krls/s10_news
```

Foram usadas 156 previsões em três folds de 52 semanas. O holdout final de 104 semanas não foi acessado. Dois pares formados por simples deslocamento de linha não eram horizontes semanais reais e foram removidos igualmente de todos os candidatos:

- `2015-08-09 → 2015-08-23`;
- `2020-08-16 → 2020-10-18`.

| Candidato | RMSE médio | Razão vs. atual | MAE médio | Gate |
|---|---:|---:|---:|---|
| atual sem notícias | 0,104741 | 1,000000 | 0,052381 | referência |
| impacto de notícias, σ=0,15 | 0,104926 | 1,002116 | 0,052278 | reprovado |
| core de notícias, σ=0,15 | 0,104953 | 1,002273 | 0,052210 | reprovado; churn 47,2% |
| todos os canais, σ=0,30 | 0,104902 | 1,002134 | 0,052320 | reprovado; churn 47,7% |

O gate exige superar o híbrido atual e o ARIMA em todos os folds, além de limitar substituições do dicionário a 40%. Nenhum candidato passou. Nos folds, 39,7% das origens não tinham notícia na janela e a cobertura média foi de apenas 27,2% das quatro fontes.

## Próxima pesquisa recomendada

1. Criar um conjunto rotulado por analistas para **pressão esperada no preço do S10**, não sentimento genérico.
2. Avaliar concordância entre anotadores, calibração e estabilidade temporal do classificador.
3. Ampliar fontes com cobertura contínua e licença auditada, mantendo indicadores explícitos de indisponibilidade.
4. Testar late fusion/stacking regularizado e defasagens de eventos, sem misturar seleção e holdout.
5. Exigir melhora em todos os folds e depois acumular dados prospectivos novos antes de revisão humana.

Os resultados atuais não sustentam alegação de economia financeira causada pelo uso de notícias.

## Pressão textual prequential

O passo seguinte foi implementado em `news_pressure.py` e `11_s10_news_pressure_backtest.py`. Um classificador logístico online usa hashing de palavras e bigramas, aprende somente rótulos cujo `target_date` já chegou e gera probabilidades `down/neutral/up`, confiança e entropia para cada origem. Os rótulos são supervisão fraca do movimento posterior do S10, com banda neutra de R$ 0,01/L; não são rótulos humanos nem evidência de que a notícia causou o movimento.

No mesmo período de desenvolvimento, a melhor representação textual (`pressure_domain_28d`) alcançou acurácia média de 60,3%, acurácia balanceada de 52,3% e macro-F1 de 52,3%. A referência de maioria calculada no próprio período foi 42,3% de acurácia e uma classe constante tem 33,3% de acurácia balanceada. Apesar disso, a late fusion com VS-ePL-KRLS obteve RMSE 0,105018 contra 0,104741 do híbrido atual e churn de 46,9%. Nenhum candidato foi autorizado para shadow.

Resultados: `reports/vs_epl_krls/s10_news_pressure/`. O holdout permaneceu fora da avaliação e o corte usado foi 2024-08-11.

## Anotação humana preparada

`12_prepare_news_annotations.py` criou um lote determinístico de 300 matérias, com 200 itens selecionados do pool de relevância e 100 controles, dois slots independentes e arquivos separados por anotador. Rótulos de máquina e identificação do controle não aparecem nas filas humanas. O manifesto mantém os hashes e `training_allowed=false` até conclusão, merge, concordância e adjudicação.

Consulte [news_annotation_protocol.md](news_annotation_protocol.md). A ausência de anotações preenchidas é agora o bloqueio humano explícito; o código não inventa esses rótulos.
