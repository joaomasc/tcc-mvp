# VS-ePL-KRLS no spread estadual

**O holdout nao foi lido.**

## A pergunta

O VS-ePL-KRLS foi reprovado prevendo o nivel do preco nacional, e a razao e
estrutural: aquela serie e dominada por saltos raros, onde uma unica semana
responde por 75% do erro quadratico. Nao ha regime a descobrir, ha um choque.

O spread estadual e outra coisa: escala pequena (desvio da variacao semanal de
0,0264 contra 0,0769 do preco), estacionario, com reversao de meia-vida de ~20
semanas e mudanca de regime. E o perfil para o qual aprendizado participativo
evolutivo com consequente KRLS foi projetado.

## Resultado

| uf | modelo | mae | rmse | directional_accuracy | n |
|---|---|---|---|---|---|
| RS | persistencia | 0.026865 | 0.034917 | 0.000000 | 156 |
| RS | linear | 0.026733 | 0.034759 | 0.537931 | 156 |
| RS | vs_epl_krls | 0.038564 | 0.047583 | 0.510345 | 156 |
| SP | persistencia | 0.017288 | 0.023864 | 0.000000 | 156 |
| SP | linear | 0.017477 | 0.023609 | 0.575540 | 156 |
| SP | vs_epl_krls | 0.056581 | 0.065546 | 0.482014 | 156 |
| MG | persistencia | 0.019449 | 0.028338 | 0.000000 | 156 |
| MG | linear | 0.020793 | 0.028957 | 0.510949 | 156 |
| MG | vs_epl_krls | 0.027413 | 0.036217 | 0.540146 | 156 |
| PR | persistencia | 0.021814 | 0.030678 | 0.000000 | 156 |
| PR | linear | 0.021789 | 0.030472 | 0.563380 | 156 |
| PR | vs_epl_krls | 0.024709 | 0.034447 | 0.507042 | 156 |

O VS superou a correcao de erro linear com ganho decidivel em **0 de 4** estados.

A comparacao e no mesmo alvo — a **variacao** do spread, nao o nivel — e nos mesmos
folds, com protocolo prequential estrito: a cada semana o modelo preve com o que ja
viu e so depois aprende aquela semana. O escalonador min-max e reajustado apenas com
o passado, porque a compatibilidade do VS exige entrada em `[0, 1]`.

## Por que ninguem ganha aqui

Repare na linha da persistencia: o modelo linear que hoje serve o estado a supera
por uma fracao de por cento, e em Minas Gerais nem isso. Nao e que o VS seja ruim
no spread — e que **em uma semana nao ha o que prever**, para ninguem.

O diagnostico por horizonte explica:

| uf | h1 | h2 | h4 | h8 | h12 | h26 |
|---|---|---|---|---|---|---|
| RS | 0.030796 | 0.033056 | 0.060235 | 0.117702 | 0.153591 | 0.145349 |
| SP | 0.025548 | 0.037558 | 0.062323 | 0.110307 | 0.133648 | 0.075727 |
| MG | 0.032774 | 0.036426 | 0.053037 | 0.079298 | 0.095560 | 0.084041 |
| PR | 0.012536 | 0.012811 | 0.017808 | 0.024459 | 0.028779 | 0.024780 |

R2 da variacao futura do spread explicada pelo desvio corrente da media. Em uma
semana ele fica em 0,01 a 0,03; em doze semanas chega a **0,154 no RS e 0,134 em
Sao Paulo — cinco vezes mais** — e volta a cair em 26. O pico em torno de doze
semanas e exatamente o que a meia-vida de reversao de ~20 semanas prediz: antes
disso o sinal ainda nao se acumulou, depois o ruido o engole.

## Conclusao

1. **O VS-ePL-KRLS nao resgata o spread no horizonte de uma semana.** Hipotese
   testada e fechada, com o mesmo rigor das demais.
2. A causa nao e o modelo: **o alvo de uma semana e quase um passeio aleatorio**, e
   a correcao linear tambem nao ganha da persistencia de forma decidivel.
3. O sinal de reversao existe e e cinco vezes maior em doze semanas. Se ha um lugar
   onde regras evolutivas merecem um teste justo nesta serie, e no horizonte longo —
   que e a mesma conclusao a que o lado comercial chegou por outro caminho.
4. **Nada e promovido.** O holdout estadual continua fechado.

