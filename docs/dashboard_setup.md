# Implantação do Brazil Economic Monitor

O dashboard AI/BI nativo foi criado como **rascunho** no workspace de validação, com definição exportável em `dashboards/brazil_economic_monitor.lvdash.json`. A implantação usa apenas tabelas Delta existentes no catálogo `workspace` e um SQL Warehouse serverless `2X-Small` já disponível. O script não cria warehouse, não publica o dashboard e não armazena IDs ou credenciais nos arquivos públicos.

A estrutura `serialized_dashboard` e o fluxo de criação seguem a [documentação oficial da API Lakeview](https://docs.databricks.com/gcp/en/dashboards/tutorials/dashboard-crud-api) e a [referência do comando Lakeview](https://docs.databricks.com/gcp/en/dev-tools/cli/reference/lakeview-commands). A [Free Edition documenta o limite de um SQL Warehouse `2X-Small`](https://docs.databricks.com/gcp/en/getting-started/free-edition-limitations); confirme a disponibilidade concreta no seu workspace antes de executar.

## Preparação

1. Execute o pipeline para disponibilizar as seis tabelas e configure o perfil local `DEFAULT` para o workspace desejado. Instale `requirements.txt` em um ambiente virtual.
2. Confirme que o workspace oferece um SQL Warehouse serverless `2X-Small` e permissão de leitura em `workspace.bcb_bronze`, `workspace.bcb_silver` e `workspace.bcb_gold`.
3. Valide sem modificar o workspace: `python dashboards/deploy_dashboard.py --validate-only`.
4. Crie ou atualize o rascunho: `python dashboards/deploy_dashboard.py`. O script imprime a URL no formato `/sql/dashboardsv3/<id>`; guarde-a fora do repositório. A execução repetida atualiza o dashboard de mesmo nome, em vez de duplicá-lo.

## Página Economic Overview

| Visualização | Fonte | Configuração |
| --- | --- | --- |
| Quatro cartões | `latest_indicators` | Meta Selic (% a.a.), IPCA mensal (% a.m.), dólar comercial (BRL/USD) e IPCA em 12 meses (%). |
| Datas de referência | `latest_indicators` | Tabela com indicador, data, valor e unidade. |
| Histórico Selic | `economic_features` | Linha de `meta_selic` por `mes`. |
| IPCA mensal | `economic_features` | Colunas de `ipca_mensal` por `mes`. |
| Histórico dólar médio | `economic_features` | Linha de `dolar_medio` por `mes`. |
| IPCA em 12 meses | `economic_features` | Linha de `ipca_12_meses` por `mes`. |

O filtro de período da página econômica atua sobre os gráficos baseados em `economic_features`. Os quatro cartões mostram a última observação disponível por série, independentemente do filtro; a tabela de datas de referência explicita o período de cada valor. A média de observações diárias e o último valor do mês são medidas diferentes. Evite apresentar o mês corrente como fechado; ele pode estar incompleto.

## Página Data Quality

| Visualização | Fonte | Configuração |
| --- | --- | --- |
| Quatro cartões de volume | Bronze e Silver | Ingeridos, válidos, rejeitados e duplicidades removidas. |
| Aproveitamento | Bronze e Silver | Cartão percentual calculado como válidos / ingeridos. |
| Distribuição | `economic_indicators` | Colunas com registros por indicador. |
| Atualização das fontes | `economic_indicators` | Tabela com frequência, unidade, última observação, última extração e dias desde a observação. |

O dashboard consulta o estado corrente das tabelas, pois o pipeline as sobrescreve. Atualizar a visualização não agenda ingestão. Uma falha entre etapas pode produzir contagens de execuções distintas; confira logs antes de considerar a reconciliação como definitiva. A métrica de duplicidades removidas é calculada como `Bronze - Silver - rejeitados`, seguindo a lógica do pipeline.

## Revisão antes de compartilhar

Confira permissões de leitura, datas, unidades e nulos. Compare as contagens SQL com os logs da execução mais recente. O rascunho foi verificado pela API com duas páginas, 19 widgets e nove datasets, e todas as 24 consultas foram executadas com sucesso no SQL Warehouse. A renderização visual e o compartilhamento devem ser revisados no navegador antes de uma eventual publicação; o script não publica automaticamente.
