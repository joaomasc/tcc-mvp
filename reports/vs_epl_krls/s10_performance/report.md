# Lucratividade, acerto de movimento e acerto de preco

Volume de referencia: **200,000 L/mes**. Todas as taxas saem de
previsoes ja emitidas; nada aqui treina ou seleciona modelo.

## As definicoes, antes dos numeros

**Lucratividade** e medida sobre os *disparos* da politica de antecipacao, na
convencao de mercado: quantos deram lucro, quanto o ganho total supera a perda
total (fator de lucro), quanto rende um disparo medio (expectativa) e quanto isso
representa sobre o gasto com combustivel. Taxa de acerto alta com expectativa baixa
e a armadilha classica; por isso os quatro numeros andam juntos.

**Acerto de movimento** exclui as semanas paradas. Acertar que nada aconteceria nao
e previsao, e incluir isso infla o numero — dois tercos das semanas desta serie sao
paradas.

**Acerto de preco** nao tem resposta unica sem escolher uma tolerancia, entao vem a
escada inteira. Escolha a tolerancia que corresponde a sua decisao, e diga qual e.

## Aviso sobre as janelas

As janelas **nao sao comparaveis entre si**. O holdout nacional foi lido duas vezes
e carrega otimismo de reuso. O desenvolvimento estadual e desenvolvimento, nao teste
cego. E o prospectivo — o unico que decide de agora em diante — esta em zero semanas
liquidadas.

### paridade — holdout nacional, 104 semanas

**Lucratividade**

- disparos: **26** em 103 semanas, 17 com lucro
- taxa de acerto do disparo: **65.4%**
- fator de lucro: **57.00**
- expectativa por disparo: **R$ 745.56**
- economia liquida: R$ 19,384.62 (ganho bruto R$ 19,730.77, perda bruta R$ 346.15)
- retorno sobre o gasto: **0.0636%**
- concentracao no maior evento: 44.0%

**Acerto de movimento**

- semanas que se moveram: **71.8%** (71 semanas)
- semanas de evento (>0.02 R$/L): **80.0%** (35 semanas)

**Acerto de preco**

- ±R$ 0.01: **41.3%**  ±R$ 0.02: **68.3%**  ±R$ 0.05: **93.3%**  ±R$ 0.10: **96.2%**
- erro mediano: R$ 0.0133/L; medio: R$ 0.0275/L
- cobertura do intervalo: 89.4% (nominal 80%)

> holdout lido duas vezes; o otimismo de reuso esta embutido

### ARIMA — holdout nacional, 104 semanas

**Lucratividade**

- disparos: **8** em 103 semanas, 6 com lucro
- taxa de acerto do disparo: **75.0%**
- fator de lucro: sem perdas registradas
- expectativa por disparo: **R$ 2,120.19**
- economia liquida: R$ 16,961.54 (ganho bruto R$ 16,961.54, perda bruta R$ -0.00)
- retorno sobre o gasto: **0.0556%**
- concentracao no maior evento: 50.3%

**Acerto de movimento**

- semanas que se moveram: **59.2%** (71 semanas)
- semanas de evento (>0.02 R$/L): **80.0%** (35 semanas)

**Acerto de preco**

- ±R$ 0.01: **51.0%**  ±R$ 0.02: **72.1%**  ±R$ 0.05: **89.4%**  ±R$ 0.10: **96.2%**
- erro mediano: R$ 0.0100/L; medio: R$ 0.0271/L

> holdout lido duas vezes; o otimismo de reuso esta embutido

### persistencia — holdout nacional, 104 semanas

**Lucratividade**

- disparos: **0** em 103 semanas, 0 com lucro
- taxa de acerto do disparo: —
- fator de lucro: sem perdas registradas
- expectativa por disparo: —
- economia liquida: R$ 0.00 (ganho bruto R$ 0.00, perda bruta R$ -0.00)
- retorno sobre o gasto: **0.0000%**

**Acerto de movimento**

- semanas que se moveram: **0.0%** (71 semanas)
- semanas de evento (>0.02 R$/L): **0.0%** (35 semanas)

**Acerto de preco**

- ±R$ 0.01: **51.9%**  ±R$ 0.02: **66.3%**  ±R$ 0.05: **91.3%**  ±R$ 0.10: **95.2%**
- erro mediano: R$ 0.0100/L; medio: R$ 0.0326/L

> holdout lido duas vezes; o otimismo de reuso esta embutido

### RS nacional+spread — desenvolvimento RS, 156 semanas

**Lucratividade**

- disparos: **60** em 154 semanas, 36 com lucro
- taxa de acerto do disparo: **60.0%**
- fator de lucro: **7.15**
- expectativa por disparo: **R$ 771.54**
- economia liquida: R$ 46,292.31 (ganho bruto R$ 53,815.38, perda bruta R$ 7,523.08)
- retorno sobre o gasto: **0.1080%**
- concentracao no maior evento: 21.8%

**Acerto de movimento**

- semanas que se moveram: **69.6%** (138 semanas)
- semanas de evento (>0.02 R$/L): **74.7%** (87 semanas)

**Acerto de preco**

- ±R$ 0.01: **20.5%**  ±R$ 0.02: **37.2%**  ±R$ 0.05: **70.5%**  ±R$ 0.10: **84.6%**
- erro mediano: R$ 0.0282/L; medio: R$ 0.0573/L

> holdout estadual nunca aberto

### RS direto — desenvolvimento RS, 156 semanas

**Lucratividade**

- disparos: **56** em 154 semanas, 29 com lucro
- taxa de acerto do disparo: **51.8%**
- fator de lucro: **4.87**
- expectativa por disparo: **R$ 680.15**
- economia liquida: R$ 38,088.46 (ganho bruto R$ 47,919.23, perda bruta R$ 9,830.77)
- retorno sobre o gasto: **0.0888%**
- concentracao no maior evento: 26.5%

**Acerto de movimento**

- semanas que se moveram: **65.2%** (138 semanas)
- semanas de evento (>0.02 R$/L): **69.0%** (87 semanas)

**Acerto de preco**

- ±R$ 0.01: **20.5%**  ±R$ 0.02: **37.2%**  ±R$ 0.05: **69.2%**  ±R$ 0.10: **84.6%**
- erro mediano: R$ 0.0298/L; medio: R$ 0.0594/L

> holdout estadual nunca aberto

### RS persistencia — desenvolvimento RS, 156 semanas

**Lucratividade**

- disparos: **0** em 154 semanas, 0 com lucro
- taxa de acerto do disparo: —
- fator de lucro: sem perdas registradas
- expectativa por disparo: —
- economia liquida: R$ 0.00 (ganho bruto R$ 0.00, perda bruta R$ -0.00)
- retorno sobre o gasto: **0.0000%**

**Acerto de movimento**

- semanas que se moveram: **0.0%** (138 semanas)
- semanas de evento (>0.02 R$/L): **0.0%** (87 semanas)

**Acerto de preco**

- ±R$ 0.01: **30.1%**  ±R$ 0.02: **44.2%**  ±R$ 0.05: **72.4%**  ±R$ 0.10: **85.3%**
- erro mediano: R$ 0.0300/L; medio: R$ 0.0597/L

> holdout estadual nunca aberto

## Prospectivo

- **paridade**: 0 semana(s) liquidada(s) de 1 previsao(oes) registrada(s).
- **regional_rs**: 0 semana(s) liquidada(s) de 1 previsao(oes) registrada(s).

Enquanto essa contagem for zero, **nenhuma taxa acima e evidencia prospectiva** —
sao todas retrospectivas, e o holdout nacional ja foi gasto.

