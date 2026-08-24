# Pressao de repasse produtor-paridade — experimento de desenvolvimento

**O holdout nao foi lido.** A avaliacao termina em 2024-08-11, pela janela congelada por data.

## A hipotese

O relatorio de paridade concluiu que o proximo ganho material exigiria capturar
os anuncios de reajuste da Petrobras no dia em que saem. A pesquisa confirma que
esses anuncios existem, sao publicos e trazem data e magnitude em R$/L — e que
saem como texto de assessoria, sem serie baixavel.

Este experimento tenta um caminho que dispensa raspagem: o anuncio e a *resposta*
da refinaria a um desvio em relacao a paridade de importacao, e os dois lados
desse desvio ja estao no painel. O ultimo preco de produtor publicado, mesmo
defasado, contra a paridade de hoje da uma medida de quanto a refinaria esta
atrasada — disponivel em tempo real.

## O mecanismo existe

Sobre o desenvolvimento inteiro (491 semanas):

- correlacao da pressao com a variacao seguinte: **-0.2661**;
- variacao media no quintil de menor pressao: **R$ +0.0461/L**;
- variacao media no quintil de maior pressao: **R$ -0.0009/L**;
- taxa de semana de evento: **55.6%** no menor quintil contra **6.1%** no maior, base 34.2%.

O sinal aponta na direcao que a economia prediz e e muito mais forte do que o
+0,097 que a defasagem de publicacao deixava disponivel. Ate aqui, a hipotese
sobrevive.

## E ainda assim nao vira previsao melhor

| spec | mae | mae_quiet | mae_event | net_savings_brl | triggered | precision |
|---|---|---|---|---|---|---|
| paridade | 0.050492 | 0.016900 | 0.078550 | 45,162 | 53 | 0.641509 |
| paridade+press | 0.051322 | 0.019559 | 0.077853 | 49,212 | 63 | 0.634921 |
| paridade+press+dpress | 0.051080 | 0.019782 | 0.077223 | 49,027 | 62 | 0.629032 |
| press_only | 0.053839 | 0.014891 | 0.086372 | 45,658 | 47 | 0.638298 |
| paridade@gate_press | 0.051770 | 0.016894 | 0.080903 | 45,162 | 53 | 0.641509 |

Nenhuma especificacao com pressao melhora o MAE de forma decidivel: o bootstrap
pareado em blocos coloca zero dentro do IC90 em todas elas. O ganho aparece so na
moeda da decisao — R$ 49,212 contra R$ 45,162 da especificacao congelada — e vem com mais
gatilhos e precisao um pouco menor. E o mesmo padrao do modelo de paridade contra
o ARIMA: **decide melhor do que preve**.

## A parte que quase enganou

A pressao correlaciona -0.3559 com o
residuo do modelo congelado, e so fracamente com os atributos que ja existem
(rpar1 -0.2084).
Lido assim, pareceria sinal novo e forte, e a conclusao seria promover.

Mas a mesma cautela que este projeto aplica aos modelos vale para os proprios
achados:

- **41% dessa correlacao desaparece** ao remover tres semanas (de -0.3559 para -0.2094);
- em posto, Spearman entrega apenas -0.1615;
- o portao de decisao nao e testavel nos folds: 9 das 156 semanas caem do lado alto.

Ou seja: o mecanismo e real, a magnitude nao esta estabelecida, e a serie tem o
mesmo tamanho amostral efetivo minusculo que ja invalidou os gates antigos.

## Conclusao

1. A pressao produtor-paridade **e um indicador antecedente real e disponivel em
   tempo real**, com mecanismo economico explicito e sem depender de raspagem.
2. Ela **nao melhora a previsao** de forma decidivel na forma linear testada.
3. O ganho na politica de compra e consistente com o mecanismo, mas cabe dentro do
   ruido que este holdout ja demonstrou produzir.
4. **Nada e promovido.** A especificacao fica pre-registrada; so semanas futuras,
   pelo ledger prospectivo, podem decidir. O holdout continua fechado.

