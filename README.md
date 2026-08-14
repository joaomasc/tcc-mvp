# Previsão do Diesel B S-10 (Brasil)

Três blocos separados:

1. **Reprodução do artigo** (mensal, dez/2012–mai/2020) — **não reproduzido** no critério de ±10% (melhor RMSE 0,077 vs 0,060).
2. **Adaptação semanal** walk-forward (h = 1, 2, 4 semanas).
3. **Produção:** ARIMA para a próxima semana.

O VS-ePL-KRLS do artigo **não foi selecionado** para produção semanal (RMSE 3,42 vs 0,073 do ARIMA).

## Previsão atual (próxima semana)

Última semana ANP: **2026-08-02**, preço **R$ 6,94/L**.

| | R$/L |
| --- | --- |
| ARIMA (produção) | **6,94** (6,90 – 6,96) |
| naive | 6,94 |

Prob. alta / estável / queda (±0,02): 9% / 61% / 30%.

Arquivo: `results/previsao_proxima_semana.json`.

## Como rodar

No macOS, LightGBM/XGBoost precisam de OpenMP: `brew install libomp`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python scripts/01_download.py
PYTHONPATH=src python scripts/02_reproducao.py
PYTHONPATH=src python -u scripts/03_semanal.py
```

## Dados

- ANP SHLP mensal/semanal Brasil (S-10)
- IPEADATA Brent (`EIA366_PBRENT366`) e câmbio (`GM366_ERC366`)
- Stooq ULSD: tentado, veio vazio nesta coleta

Distribuição ANP só até 17/08/2020. Buraco de pesquisa 18/08/2020–17/10/2020.
