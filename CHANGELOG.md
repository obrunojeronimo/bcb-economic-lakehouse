# Histórico de versões

## 1.0.0 — 26/11/2026

Primeira release do BCB Economic Lakehouse.

- Pipeline Full Refresh de cinco séries públicas do SGS, organizado nas camadas Bronze, Silver e Gold, com seis tabelas Delta no catálogo `workspace`.
- Dashboard AI/BI Brazil Economic Monitor, consultas SQL, documentação de arquitetura, dicionário de dados e guia de reprodução.
- Execução dos componentes Python como módulos a partir da raiz do repositório, incluindo `python -m src.pipeline` e `python -m dashboards.deploy_dashboard`.
- Suíte com seis testes automatizados: quatro para configuração e extração e dois para a orquestração.

### Limitações conhecidas

- As tabelas são sobrescritas individualmente; uma falha pode deixá-las em estados de execuções diferentes.
- Os testes automatizados não exercitam a API SGS, o Databricks nem as transformações Spark de ponta a ponta.
- A reprodução operacional requer acesso à API SGS e a um workspace Databricks compatível, com perfil local `DEFAULT` e permissões no catálogo `workspace`.
