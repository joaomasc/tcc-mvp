# Estados servidos e pooling hierarquico do spread

**O holdout nao foi lido.** Avaliacao ate 2024-08-11.

## Uma planilha, N estados

A ANP publica as 27 unidades da federacao no mesmo arquivo de 12,5 MB. O download
acontece uma vez e a previsao nacional, que e identica para todos, e calculada uma
vez. O custo marginal de mais um estado e a leitura de uma tabela.

## O encolhimento, e o que ele deveria fazer

A reversao do spread estimada num estado com poucos postos pesquisados e em boa
parte ruido. O estimador de efeitos aleatorios de DerSimonian-Laird separa a
variancia *entre* estados da incerteza *dentro* de cada estimativa e devolve o peso
de Bayes empirico `tau^2 / (tau^2 + se^2)`. Quando os estados de fato diferem, cada
um fica com o proprio numero; quando a diferenca cabe dentro do erro de estimativa,
todos convergem para o valor comum. Nenhum limiar arbitrario decide isso.

| uf | postos | peso_proprio | mae_local | mae_pooled | mae_postos | ganho_pooled | ganho_postos | decidivel_postos |
|---|---|---|---|---|---|---|---|---|
| SP | 1,013 | 0.938684 | 0.049454 | 0.049429 | 0.049439 | 0.000504 | 0.000306 | False |
| MG | 368.500000 | 0.905973 | 0.058432 | 0.058505 | 0.057556 | -0.001240 | 0.014998 | True |
| RS | 261.500000 | 0.957738 | 0.057294 | 0.057310 | 0.057263 | -0.000286 | 0.000541 | False |
| PR | 231.500000 | 0.977424 | 0.055381 | 0.055385 | 0.055395 | -0.000073 | -0.000258 | False |
| BA | 199.000000 | 0.807074 | 0.113261 | 0.111945 | 0.111449 | 0.011617 | 0.015999 | True |
| SC | 174.000000 | 0.942392 | 0.055271 | 0.055235 | 0.055623 | 0.000645 | -0.006371 | False |
| GO | 117.000000 | 0.881638 | 0.066321 | 0.066361 | 0.066147 | -0.000605 | 0.002629 | True |
| PA | 97.000000 | 0.899759 | 0.079308 | 0.079283 | 0.080006 | 0.000308 | -0.008800 | False |
| MT | 79.000000 | 0.856643 | 0.083198 | 0.083951 | 0.083097 | -0.009045 | 0.001223 | False |
| RO | 51.000000 | 0.904289 | 0.063816 | 0.063497 | 0.063874 | 0.005004 | -0.000900 | False |

Encolhimento pelo conjunto: melhora em **5 de 10**
estados, decidivel em **3**.

Ponderacao por numero de postos: melhora em **6 de 10** estados, decidivel em **3**.

## O que a medicao desmentiu

A hipotese era que estados com poucos postos pesquisados se beneficiariam mais do
encolhimento. **Nao se sustentou:** a correlacao entre numero de postos e ganho do
pooling e +0.0088, ou seja, nula.

A razao aparece nos pesos: quase todos ficam acima de 0,8, porque `tau^2` — a
variancia *entre* estados — e grande em relacao ao erro de cada estimativa. Em
portugues: os estados **realmente** revertem em velocidades diferentes, entao ha
pouco a tomar emprestado. E o proprio estimador dizendo que o pooling nao e o
remedio aqui.

O erro do diagnostico foi confundir dois tamanhos de amostra. O numero de postos
afeta o ruido de **cada observacao semanal**; a reversao `kappa` e estimada sobre
**centenas de semanas**, e por isso ja chega precisa em todo estado. Pooling resolve
poucas observacoes, nao observacoes ruidosas.

## Onde o tamanho da amostra de fato importa

Medido nos dez estados: as semanas do quartil inferior de postos pesquisados tem
**cerca de 1,9x** a volatilidade do spread das demais — de 1,3x em Sao Paulo a 2,6x
em Mato Grosso. A ANP publica esse numero em toda linha, e o modelo o ignorava.

A correcao e minimos quadrados ponderados pelo numero de postos, que e o peso
estatisticamente correto para a media de uma amostra. E o mesmo insight do
diagnostico original, aplicado no lugar certo.

## Conclusao

1. Servir outro estado nao exige pesquisa nova — exige rodar. O download e a
   previsao nacional sao compartilhados; o custo marginal e ler uma tabela.
2. **O encolhimento pelo conjunto nao e o caminho** para estados pequenos, e a
   medicao diz por que. Fica registrado como hipotese fechada.
3. Ponderar por numero de postos usa uma informacao que o arquivo ja entrega.
4. **Nada e promovido.** O holdout estadual continua fechado.

