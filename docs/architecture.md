# Arquitetura do produto S10 Intelligence

## Princípio

O produto separa pesquisa, promoção e serving. Nenhuma requisição HTTP treina, atualiza ou promove modelos. A API carrega uma única release imutável, verifica seu SHA-256 antes de desserializar e recusa servir uma previsão vencida.

```mermaid
flowchart LR
    ANP["ANP oficial semanal"] --> EX["Extração S10 nacional + validação de schema"]
    EX --> LED["Ledger append-only encadeado por SHA-256"]
    EX --> REL["Release imutável"]
    SEL["Seleção temporal + holdout"] --> REL
    REL --> SVC["S10ProductService"]
    SVC --> API["API read-only"]
    API --> OBS["Health, readiness, métricas e logs JSON"]
    REL -. "previsão e resultado" .-> SH["Challenger em shadow"]
    NEWS["Notícias com proveniência"] -. "research only" .-> SH
```

## Componentes

| Componente | Responsabilidade | Falha segura |
|---|---|---|
| `anp_official.py` | extrair uma observação Brasil/S10/R$/L e registrar hash da fonte | rejeita schema, unidade, geografia, data ou preço inesperado |
| `audit.py` | ledger canônico encadeado | rejeita conteúdo, sequência ou elo adulterado |
| `production.py` | ARIMA primário, intervalos, fallback e challenger | persistência em saída não finita/implausível |
| `product.py` | integridade, atualidade, evidência e cenários | readiness 503 quando a previsão vence |
| `api.py` | JSON dos modelos, autenticação, limites, headers, telemetria e OpenAPI | sem endpoints mutáveis nem frontend |
| `procurement.py` | replay causal de uma política pré-fixada | valida alinhamento origem/alvo e semanas sem gaps |
| `shadow.py` | avaliação prospectiva congelada | nunca promove automaticamente |

## Fluxo semanal

1. Baixar a planilha da página institucional da ANP e conservar o arquivo bruto.
2. Executar `14_s10_ingest_official.py` apontando para uma saída nova; sobrescrita é recusada.
3. Conferir fonte, hash, erro, cobertura, fallback, health e round-trip.
4. Atualizar o shadow com a mesma planilha; data e preço são comparados ao conteúdo oficial.
5. Rodar a suíte completa e os smoke tests da API.
6. Publicar a release por um ponteiro/registry da plataforma, mantendo rollback para o hash anterior.

## Escala

O artefato atual é pequeno e a inferência é CPU-bound curta. Em container, cada worker carrega uma cópia em memória. Começar com um worker por container e escalar horizontalmente; somente depois de medir carga real decidir número de réplicas. TLS, autenticação de usuários, secrets, logs e alertas devem ser terminados/centralizados pela plataforma.
