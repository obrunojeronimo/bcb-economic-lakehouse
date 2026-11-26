# Decisões de engenharia

## Fonte e extração

O projeto usa a API pública SGS do Banco Central, com cinco séries definidas em `config/series.json` e período iniciado em 01/01/2020. `requests.Session` reutiliza conexões, trata HTTP 429/5xx com `Retry` e aplica timeout de 60 segundos. Isso simplifica a reprodução e preserva dados reais. A extração é sequencial e falha se uma resposta for vazia ou inválida; paralelismo ou extração incremental exigiriam controle adicional de limite, cursor e reprocessamento.

## Medallion e contratos

Bronze guarda data e valor como texto, além de URL e horário de origem. Silver converte data, valor decimal e timestamp, separa rejeições e identifica valores conflitantes para a mesma série/data antes de deduplicar. Essa ordem evita escolher arbitrariamente entre valores numéricos divergentes. A rejeição registra apenas a primeira regra que falhou. Não há regras de faixa econômica, calendário esperado ou comparação com fonte independente. Gold atende três usos: histórico mensal, último indicador e base mensal de atributos. A média mensal de séries diárias é aritmética simples; taxas mensais e `meta_selic` na base de atributos usam o último valor do mês. Não há imputação de ausentes.

## Persistência e execução

As seis tabelas são Delta no catálogo `workspace`, em três esquemas. O pipeline usa **Full Refresh com `overwrite`** em cada tabela, em ordem Bronze → Silver → Gold. É simples de executar e reflete revisões históricas da fonte, mas relê todo o período e substitui snapshots anteriores. Delta oferece transações por tabela; **não existe garantia de atomicidade entre todas as camadas**. Uma falha após uma escrita pode deixar tabelas de execuções diferentes. Alternativas para uma evolução: ingestão incremental com watermark e `MERGE`, identificador de execução/linhagem, publicação por versões e promoção controlada após validação. Nenhuma dessas alternativas está implementada.

## Plataforma e autenticação

`src/connection.py` cria sessão Databricks Connect em serverless e usa o perfil local `DEFAULT`. Isso evita armazenar credenciais no repositório, mas pressupõe esse perfil, um workspace compatível, permissões no catálogo `workspace` e conectividade. As dependências Python estão fixadas em `requirements.txt`. Fixar versões torna o ambiente mais previsível, mas requer atualização consciente quando o runtime muda. Não há deploy de jobs nem agendamento definido neste repositório.

## Testes e observabilidade

Quatro testes unitários simulam a sessão HTTP e cobrem configuração e casos básicos da extração. Dois testes adicionais simulam a sessão Spark para verificar a ordem da orquestração e o encerramento após falha. Os seis testes rodam sem Databricks e sem chamada real à API. Não há testes automatizados de integração para Bronze, Silver, Gold, permissões, esquema ou reconciliação ponta a ponta. O pipeline registra duração por etapa e total; Silver imprime contagens de válidos, rejeitados e duplicidades. Esses números são diagnóstico de uma execução, sem armazenamento histórico de métricas. As consultas em `sql/data_quality.sql` são verificações manuais adicionais, não gates automáticos.

## Interpretação dos indicadores

`monthly_indicators` mistura séries originalmente diárias e mensais sob uma referência mensal. A linha de um mês pode conter apenas parte das observações esperadas, especialmente no mês corrente. `economic_features` também pode ter nulos quando uma série ainda não publicou uma observação naquele mês. Comparações e dashboards devem mostrar data da última observação e filtrar meses fechados quando necessário. O percentual de 100% relatado em 26/11/2026 refere-se somente às regras implementadas naquela execução.
