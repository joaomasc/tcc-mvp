# Pesquisa aplicada à profissionalização

Decisões de arquitetura foram confrontadas com fontes primárias e oficiais:

- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) e [Playbook](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook): governar, mapear, medir e gerenciar risco continuamente. Aplicação: model card, gates, shadow, claim boundaries e revisão humana.
- [NIST Secure Software Development Framework SP 800-218](https://csrc.nist.gov/pubs/sp/800/218/final): integrar práticas seguras ao ciclo de desenvolvimento. Aplicação: CI, dependências, threat model, release imutável e backlog de supply chain.
- [Google Cloud, MLOps continuous delivery and automation](https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning): validação de dados/modelos, metadata, triggers e CI/CD. Aplicação: separar seleção, release, serving e monitoramento.
- [MLflow Model Registry workflows](https://mlflow.org/docs/latest/ml/model-registry/workflow): versões, tags, aliases e ambientes. Recomendado como próximo passo, não adicionado como dependência pesada ao runtime.
- [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/): métricas, logs e traces correlacionáveis. O produto já emite logs JSON e métricas; collector/tracing ficam para a plataforma.
- [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/): consumo irrestrito e misconfiguration. Aplicação: rate limit, body limit, host allowlist, produção sem docs e security headers.
- [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/): HTTPS, startup, restart, replicação e memória. Aplicação: container e separação explícita da terminação TLS.
- [ANP, últimas semanas pesquisadas](https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/levantamento-de-precos-de-combustiveis-ultimas-semanas-pesquisadas) e [série histórica](https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis): fonte institucional e cadência semanal.
- [CycloneDX ML-BOM](https://cyclonedx.org/guides/OWASP_CycloneDX-Authoritative-Guide-to-AI-ML-BOM-en.pdf): próximo passo para inventário de modelo, dados, componentes e proveniência.

