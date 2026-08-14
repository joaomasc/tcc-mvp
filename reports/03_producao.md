# Bloco 3 — Modelo final de produção

**Recomendado para 1 semana à frente: ARIMA** (menor RMSE walk-forward).

O VS-ePL-KRLS permanece no repositório como reprodução/adaptação do artigo. Com 18 features semanais ele perdeu feio para persistência e **não deve ser usado em produção** nesse desenho.

## Previsão da próxima semana

Preço médio nacional de **revenda** do Diesel B S-10 (ANP), R$/L.

- Semana observada: **2026-08-02**
- Preço observado: **6,94**
- Modelo: ARIMA
- Previsão pontual: **6,936**
- P10–P90 (quantis dos últimos 80 resíduos walk-forward): **6,902 – 6,956**
- Prob. alta / estável / queda (banda ± R$ 0,02/L): **8,8% / 61,3% / 30,0%**
- Naive (último valor): 6,94

Leitura: a série semanal se comporta quase como passeio aleatório. O ARIMA está essencialmente dizendo “fica onde está”, com intervalo estreito.

## Ranking h=1 (RMSE)

1. ARIMA 0,073
2. ARIMAX (Brent + USD/BRL defasados) 0,075
3. naive 0,079
4. média móvel 0,139
5. XGBoost 0,239
6. LightGBM 0,248
7. VS-ePL-KRLS (18d) 3,42 — descartado
8. LSTM 4,08 — descartado

## Model card

- Alvo: preço médio nacional de revenda do Diesel B S-10 (ANP), não o preço de um posto.
- Horizonte: 1 semana à frente.
- Atualização: reajustar o ARIMA a cada nova semana da ANP (arquivo `semanal-brasil-desde-2013.xlsx`).
- Exógenas: Brent e USD/BRL melhoram pouco (ARIMAX ≈ ARIMA).
- Distribuição ANP: só na reprodução mensal do artigo; série acaba em 17/08/2020.
- Buraco ANP: 18/08/2020–17/10/2020, não imputado no alvo.
- VS-ePL-KRLS: reprodução mensal **não atingiu** ±10% do RMSE publicado (0,077 vs 0,060). Semanal 18-d falhou.
- Quando desconfiar: RMSE móvel de 12 semanas do ARIMA subir de forma persistente acima de ~0,12, ou salto de política de preços da Petrobras na semana corrente (o modelo não vê o anúncio intra-semana).

Este bloco não declara reprodução do artigo. A reprodução está em `reports/01_reproducao.md`.
