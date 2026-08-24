# Segurança e threat model

## Ativos e fronteiras

Ativos críticos: planilhas ANP brutas, fingerprints, artefatos joblib, manifests, ledgers, previsões e chaves da API. Entradas externas são planilhas, parâmetros HTTP e configuração de ambiente. O arquivo joblib cruza uma fronteira de confiança porque sua desserialização usa pickle.

## Controles implementados

- SHA-256 obrigatório antes de carregar uma release pelo serviço;
- arquivos de release imutáveis e gravação atômica;
- ledger append-only com JSON canônico, sequência e hash anterior;
- API somente leitura, schema estrito e campos extras proibidos;
- chave via ambiente obrigatória em modo `production`, comparação em tempo constante;
- rate limit, payload máximo, host allowlist e request ID saneado;
- CSP, `nosniff`, `DENY`, `no-referrer`, Permissions Policy e `no-store`;
- container sem root, filesystem read-only, capabilities removidas e `no-new-privileges`;
- previsão vencida retorna readiness 503 e não é entregue pelo endpoint de forecast;
- nenhuma chave, e-mail ou dado pessoal é gravado em log pela API.

## Riscos residuais antes de go-live público

1. Joblib/pickle só pode vir do pipeline confiável. Um hash confirma identidade, não torna um produtor malicioso seguro.
2. API key é adequada para piloto interno, não substitui identidade por usuário, RBAC, rotação e auditoria de acesso.
3. O rate limiter é por processo; produção pública precisa de gateway distribuído.
4. TLS, WAF, secrets manager, retenção de logs e alertas dependem da plataforma de implantação.
5. Dependências precisam de SBOM e varredura contínua de vulnerabilidades em CI.
6. Falta pentest independente e revisão da imagem efetivamente implantada.

## Gate de go-live

- TLS obrigatório e API privada por padrão;
- chave rotacionável em secrets manager, sem valor em imagem ou repositório;
- image digest, SBOM, assinatura/proveniência de build e vulnerability scan aprovados;
- teste de carga, restart, rollback e restauração do ledger no ambiente-alvo;
- alertas de 5xx, latência, readiness, stale forecast e hash mismatch;
- responsável de plantão e procedimento de incidente definidos.

