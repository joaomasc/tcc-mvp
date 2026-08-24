# Relatório de implementação do VS-ePL-KRLS

## Escopo

Esta é uma implementação independente em Python/NumPy, com API prequential, criada a partir do [artigo aberto](https://pmc.ncbi.nlm.nih.gov/articles/PMC8147597/), da [dissertação](https://www.maxwell.vrac.puc-rio.br/52507/52507.PDF) e da [versão em português](https://ojs.sba.org.br/index.php/cba/article/download/1039/1030/2819). Nenhum código do repositório GPL `evolvingfuzzysystems` foi incorporado.

## Pontos diretamente extraídos das fontes

1. Compatibilidade da regra: `rho_i = 1 - ||x-v_i||/m`.
2. Excitação: `a_i <- a_i + beta(1-rho_i-a_i)`.
3. Criação quando o menor índice de excitação supera `tau`.
4. Centro literal: `v_i <- v_i + alpha * v_i**(1-a_i) * (x-v_i)`.
5. Compatibilidade entre regras: `1 - mean(abs(v_i-v_j))`.
6. Limiares do Algoritmo 1 da dissertação: `tau=beta_anterior` e `gamma=1-beta_anterior`.
7. RBF local `exp(-||x-d||²/(2 nu²))` e soma global ponderada.
8. Inicialização KRLS, inversão em bloco `Q`, residual `r=lambda+1-z.T@g` e expansão dos coeficientes.
9. Novidade `psi=min ||x-d||`, `delta=nu/10` e inserção condicionada à melhora do erro.
10. Passo variável: dividir `beta` por `alpha_vs1` em erro alto, multiplicar por `alpha_vs2` em erro baixo.
11. Constantes comuns reportadas: `alpha=0.01`, `beta0=0.18`, `sigma=0.05`, `lambda=1e-4`, `nu0=0.5`; `gamma_bar` e fatores VS variam por experimento.

## Decisões de engenharia explícitas

- **Ordem prequential:** a saída global é calculada antes do alvo atual. A excitação usa `beta(k-1)` e o beta recém-calculado vale para o próximo passo. Isso combina as dependências matemáticas com a ordem do Algoritmo 1.
- **Ativação global:** compatibilidades positivas normalizadas por sua soma; se todas forem zero, pesos uniformes. A fonte denomina `Lambda` mas não oferece, no trecho formal, uma alternativa inequívoca.
- **Erro normalizado:** `error_normalization="none"` assume alvo previamente normalizado. `fixed`, `running_range` e `running_std` são extensões online e nunca consultam alvos futuros.
- **Amostra coerente:** aplica RLS no vetor de kernels com dicionário fixo. A fonte detalha a inserção de centros, mas não uma política completa para repetidas amostras coerentes.
- **Dicionário cheio:** `oldest`, `least_used` ou `none`; após substituição, o sistema é reconstruído com replay limitado. O artigo não prescreve descarte.
- **Fusão de consequentes:** mantém a regra mais ativada, combina centros/dispersões ponderados, absorve dicionários até o limite e recalcula pelo replay. A fonte define a média dos centros, mas não como fundir dois estados KRLS.
- **Larguras variáveis:** usa a derivada analítica positiva da RBF em relação a `nu`, limita a variação e reconstrói `Q`. O sinal na cópia/OCR da equação de gradiente é ambíguo.
- **Centro alternativo:** `center_update="paper"` é o padrão literal. `"compatibility"` implementa a forma ePL comum e evita que um centro exatamente zero fique congelado.
- **Limites:** número de regras e dicionário foram adicionados para memória previsível e segurança operacional.
- **Recuperação de beta:** `beta_recovery_rate>0` cria um piso de recuperação proporcional à severidade quando o erro normalizado ultrapassa o limiar. O padrão zero preserva a regra VS implementada a partir da fonte.
- **Utilidade recente:** `dictionary_usage_decay<1` faz a política `least_used` privilegiar atividade recente, em vez de contagens acumuladas desde o início.
- **Híbrido residual:** o VS recebe como alvo `y_t-base_t` somente quando `y_t` fica disponível. Peso e limite absoluto da correção são guardrails de engenharia, não equações do artigo.
- **Exógenas causais:** Brent, USD/BRL, Brent em reais e reajustes entram exclusivamente em colunas defasadas no experimento de desenvolvimento. Elas não fazem parte do contrato atual do bundle.

## Limites para alegar reprodução exata

Os valores iniciais `tau0=0.82` e `gamma0=0.18` citados na tabela do artigo são opostos às relações `tau=beta` e `gamma=1-beta` do Algoritmo 1 da dissertação. A implementação segue o algoritmo formal e permite limiares fixos para a convenção alternativa. A notação `erro normalizado` também não vem acompanhada de uma transformação online inequívoca. Esses pontos impedem afirmar equivalência bit a bit sem o código MATLAB original.

Além disso, os dados semanais exatos, filtros geográficos, revisões do arquivo e transformação de atributos precisam ser idênticos. O pipeline operacional novo restringe o escopo ao Diesel B S10 e não depende de inferir equivalência com S500 ou diesel genérico.

## Como verificar contra o artigo

1. Obter e versionar o arquivo ANP original e seu hash.
2. Confirmar preço (revenda/distribuição), cobertura Brasil e regra semanal.
3. Construir as janelas de 2 e 4 semanas com a mesma normalização.
4. Separar janeiro/2013–dezembro/2018 para treino e janeiro/2019–maio/2020 para teste.
5. Fixar os parâmetros da Tabela 5 para cada produto/horizonte.
6. Rodar as duas convenções de `tau/gamma` e os modos de centro, registrando qual reproduz a evolução de regras publicada.
7. Comparar RMSE, MAE, NDEI, número médio de regras e gráficos de evolução.
8. Verificar tolerâncias, depois fazer revisão independente e teste estatístico na mesma amostra.

## Resultado sintético desta implementação

O comando `python examples/synthetic_regression.py --random-state 42` grava a tabela medida em `reports/vs_epl_krls/synthetic/metrics.csv`. A mudança de regime é conhecida e a comparação usa exatamente o mesmo fluxo para o modelo VS e sua ablação de beta fixo. O resultado serve como teste funcional, não como substituto da reprodução ANP.

Na execução com 480 pontos, após aquecimento de 48 pontos, o VS obteve RMSE 0.12133, a ablação fixa 0.21271 e a persistência 0.03527. Portanto, o VS respondeu melhor que a ablação, mas perdeu amplamente para o baseline simples.

## Reprodução S10 de 2 e 4 semanas

Com a planilha local, fim em maio/2020, divisão temporal 80/20, atualização atrasada pelo horizonte e os hiperparâmetros S10 reportados na dissertação, os RMSEs medidos foram:

| Série | 2 semanas | 4 semanas | Artigo (2 / 4) |
|---|---:|---:|---:|
| S10 | 0.54629 | 0.87526 | 0.03486 / 0.05972 |

Esses desvios são materialmente grandes e piores que persistência (0.05429 / 0.10263). Eles demonstram que aplicar parâmetros publicados a um painel de lags não comprovadamente idêntico não constitui reprodução. As causas a isolar incluem os atributos usados no trabalho original, a convenção `tau/gamma`, a normalização do erro e as políticas KRLS não explicitadas. Esses números não são usados para selecionar o bundle operacional de uma semana.

## Seleção S10 para produção de uma semana

Para uso operacional foi definido um problema separado: média nacional semanal de revenda do Diesel B S10 e horizonte de uma semana. Foram usadas 702 observações até 2026-08-09, três folds expansivos de 52 semanas para seleção e calibração e holdout final de 104 semanas. Os escalonadores são ajustados apenas no passado de cada fold e o rótulo de cada origem só é ensinado quando sua data-alvo já chegou.

O candidato VS congelado usa seis lags de preço, alvo em variação semanal, `alpha=0.26`, `beta0=0.18`, `alphaVS1=0.94`, `alphaVS2=0.74`, limiar de erro normalizado 0.5, RBF 0.15, até 20 regras e dicionário máximo 20. No holdout obteve RMSE 0.09382 contra 0.09563 da persistência, com `p=0.0395`; usou 13 regras, saturou o dicionário e manteve `beta` quase sempre no piso `1e-4`. Venceu a persistência nos três folds, mas o ganho final de 1,90% ficou ligeiramente abaixo do gate pré-fixado de 2%. Portanto não foi promovido. Ajustar `beta_min` agora contaminaria o holdout já observado; essa hipótese ficou reservada para uma janela futura independente.

O ARIMA obteve RMSE 0.08145, 14,8% abaixo da persistência; ainda assim, `p=0.1338` exige rollout controlado. O intervalo P10–P90, calibrado com 156 resíduos de validação, cobriu 92,3% do holdout para nominal de 80%. O bundle de produção mantém ARIMA como primário, VS em shadow mode, Ridge/ensemble para diagnóstico, fallback robusto, verificação de schema/cadência, fingerprint, serialização atômica e health report.

Essa arquitetura é uma decisão de engenharia baseada em medição, não uma conclusão de que VS-ePL-KRLS seja inferior em geral. Uma promoção futura exige novos folds temporais, holdout independente, ganho mínimo e teste estatístico, conforme o [runbook](s10_production_runbook.md).

## Auditoria do próximo challenger

Depois de aberto o holdout, todas as novas hipóteses foram avaliadas somente nos três folds de desenvolvimento originais, encerrados no índice 585. O manifest registra `holdout_evaluated=false` e `production_promotion_allowed=false`.

Foram testados 13 candidatos diretos e nove híbridos: recuperação de `beta`, pisos maiores, forgetting, utilidade recente, dicionários de 30/40 elementos, atributos exógenos defasados e correção residual do ARIMA. O candidato VS direto original continuou primeiro. A melhor média híbrida (`hybrid_lags_paper`) não foi estável: melhorou em média, mas piorou o ARIMA em 7,3% no segundo fold.

O gate robusto selecionou para shadow `hybrid_dynamics_conservative`, que usa peso 0,5 e limite de R$ 0,10/L na correção. Nos três folds, seu RMSE médio foi 0,10456 contra 0,10506 do ARIMA; a razão média foi 0,9946 e a pior 0,9981. O ganho de cerca de 0,54%, 20 regras e churn de 34,4% não justificam promoção. O resultado demonstra por que média isolada não é gate suficiente.

## Endurecimento operacional 1.1

O artefato 1.1 limita a calibração aos últimos 156 resíduos, incorpora o erro somente após a realização, mede cobertura e MAE online, alerta cobertura inferior a 70% após 20 semanas, expõe churn KRLS e rejeita artefatos de contrato anterior. A suíte final contém 174 testes, 93,43% de cobertura do código em `src` e um stress de 1.500 amostras com três regimes, limites de regras/dicionário e finitude verificados.

O critério de novidade do dicionário foi implementado independentemente, mas segue a motivação de dependência linear aproximada do KRLS esparso descrita no [trabalho original de Engel et al.](https://citeseerx.ist.psu.edu/document?doi=ed5d2aca56aa23f846e793160373bc74a431431c&repid=rep1&type=pdf). Políticas de substituição ao atingir o teto continuam sendo extensões necessárias para memória limitada. Métodos conformais fortemente adaptativos, como [Bhatnagar et al.](https://proceedings.mlr.press/v202/bhatnagar23a.html), são uma direção futura; o bundle atual implementa apenas calibração empírica por janela móvel.
