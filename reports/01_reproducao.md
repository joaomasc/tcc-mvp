# Bloco 1 — Reproducao do artigo

Janela historica: dezembro/2012 a maio/2020, Diesel S-10 nacional, previsao mensal.
Entrada: `[preco_distribuicao(t), preco_revenda(t)]`. Alvo: `preco_revenda(t+h)`.
Normalizacao min-max apenas no treino. Teste: prever antes de atualizar.

## Criterio (fixado antes de rodar)
REPRODUZIDO se RMSE, MAE e NDEI ficarem a ±10% dos valores publicados e o numero de regras coincidir.

## Resultados

   experimento  horizonte convencao    VS       rmse        mae       ndei  n_regras        veredito  rmse_artigo  mae_artigo  ndei_artigo
  h1_tabela_vs          1    tabela  True   0.100214   0.075182   0.221224       1.0 NAO REPRODUZIDO      0.05953     0.05158      0.13430
 h1_tabela_epl          1    tabela False   0.100214   0.075182   0.221224       1.0 NAO REPRODUZIDO      0.16747     0.11815      0.37785
   h1_texto_vs          1     texto  True   0.077497   0.062416   0.171075       1.0 NAO REPRODUZIDO      0.05953     0.05158      0.13430
  h1_texto_epl          1     texto False   1.582716   1.514321   3.493855       3.0 NAO REPRODUZIDO      0.16747     0.11815      0.37785
  h6_tabela_vs          6    tabela  True   0.855619   0.829175   1.888783      61.0 NAO REPRODUZIDO      0.10869     0.08366      0.26269
 h6_tabela_epl          6    tabela False   0.155372   0.095376   0.342985       1.0         ablacao      0.10869     0.08366      0.26269
   h6_texto_vs          6     texto  True   0.159504   0.100313   0.352105       1.0 NAO REPRODUZIDO      0.10869     0.08366      0.26269
  h6_texto_epl          6     texto False   1.886319   1.862023   4.164059       2.0         ablacao      0.10869     0.08366      0.26269
 h12_tabela_vs         12    tabela  True   0.992456   0.947908   2.190852      53.0 NAO REPRODUZIDO      0.12490     0.10133      0.33491
h12_tabela_epl         12    tabela False 194.115427 135.246007 428.510876       1.0         ablacao      0.12490     0.10133      0.33491
  h12_texto_vs         12     texto  True  82.519632  61.015724 182.162543       1.0 NAO REPRODUZIDO      0.12490     0.10133      0.33491
 h12_texto_epl         12     texto False   1.308816   0.884003   2.889219       2.0         ablacao      0.12490     0.10133      0.33491

Melhor configuracao em h=1: **h1_texto_vs** com veredito **NAO REPRODUZIDO**.

Nenhuma afirmacao de reproducao e feita fora desta tabela. Os numeros deste bloco
nao se transferem automaticamente para a frequencia semanal (bloco 2).