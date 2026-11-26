# Dicionário de dados

Todas as tabelas são Delta no catálogo `workspace`. Os tipos abaixo seguem os esquemas explícitos de Bronze e as expressões PySpark de Silver e Gold; nulabilidade física não é imposta por `NOT NULL`. As seis tabelas são sobrescritas a cada execução.

## `workspace.bcb_bronze.sgs_raw`

Granularidade: uma observação recebida do SGS por série e data, sem deduplicação.

| Campo | Tipo | Significado |
| --- | --- | --- |
| `codigo_serie` | INT | Código da série SGS. |
| `indicador` | STRING | Nome configurado em `config/series.json`. |
| `frequencia` | STRING | Frequência declarada na configuração. |
| `unidade` | STRING | Unidade declarada na configuração. |
| `data_raw` | STRING | Data original da API, em `dd/MM/yyyy`. |
| `valor_raw` | STRING | Valor original da API, sem conversão. |
| `fonte` | STRING | URL da série consultada. |
| `extraido_em` | STRING | Instante UTC da extração em formato ISO 8601. |

## `workspace.bcb_silver.economic_indicators`

Granularidade: uma linha válida por (`codigo_serie`, `data`). A unicidade é obtida por `dropDuplicates`, sem constraint física declarada.

| Campo | Tipo | Significado |
| --- | --- | --- |
| `codigo_serie` | INT | Código SGS. |
| `indicador` | STRING | Nome da série. |
| `frequencia` | STRING | Frequência configurada. |
| `unidade` | STRING | Unidade configurada. |
| `data` | DATE | Data convertida de `data_raw`. |
| `valor` | DECIMAL(18,6) | Valor numérico convertido de `valor_raw`. |
| `fonte` | STRING | URL de origem. |
| `extraido_em` | TIMESTAMP | Instante de extração convertido. |

## `workspace.bcb_silver.data_quality`

Granularidade: uma linha Bronze rejeitada por falha em código, data, valor ou timestamp. A tabela pode estar vazia. A primeira falha na ordem das regras determina `motivo_rejeicao`.

| Campo | Tipo | Significado |
| --- | --- | --- |
| `codigo_serie` | INT | Código SGS original. |
| `indicador` | STRING | Nome configurado. |
| `frequencia` | STRING | Frequência configurada. |
| `unidade` | STRING | Unidade configurada. |
| `data_raw` | STRING | Data original. |
| `valor_raw` | STRING | Valor original. |
| `fonte` | STRING | URL de origem. |
| `extraido_em` | TIMESTAMP | Timestamp convertido; pode ser nulo quando inválido. |
| `data` | DATE | Data convertida; pode ser nula quando inválida. |
| `valor` | DECIMAL(18,6) | Valor convertido; pode ser nulo quando inválido. |
| `motivo_rejeicao` | STRING | `Codigo da serie invalido`, `Data invalida`, `Valor invalido` ou `Timestamp de extracao invalido`. |

## `workspace.bcb_gold.monthly_indicators`

Granularidade: uma linha por (`mes`, `codigo_serie`, `indicador`, `unidade`, `frequencia`). `mes` é o primeiro dia do mês de `data`.

| Campo | Tipo | Significado |
| --- | --- | --- |
| `mes` | DATE | Mês de referência. |
| `codigo_serie` | INT | Código SGS. |
| `indicador` | STRING | Nome da série. |
| `unidade` | STRING | Unidade da série. |
| `frequencia` | STRING | Frequência original. |
| `valor_medio` | DECIMAL, escala derivada | Média aritmética de `valor`, arredondada a seis casas. |
| `valor_minimo` | DECIMAL(18,6) | Mínimo observado no mês. |
| `valor_maximo` | DECIMAL(18,6) | Máximo observado no mês. |
| `ultimo_valor` | DECIMAL(18,6) | Valor associado à maior `data` no mês (`max_by`). |
| `ultima_observacao` | DATE | Maior data observada no mês. |
| `observacoes` | BIGINT | Número de linhas Silver no grupo. |

O tipo preciso de `valor_medio` depende da inferência de `avg` e `round` pelo runtime Spark; confirme com `DESCRIBE TABLE` no workspace. Para séries mensais, `observacoes` costuma ser uma, mas isso não é garantia de publicação da fonte.

## `workspace.bcb_gold.latest_indicators`

Granularidade: uma linha por `codigo_serie`, escolhida pela maior `data` com `row_number`. Possui os **mesmos oito campos e tipos de `economic_indicators`**: `codigo_serie` INT, `indicador` STRING, `frequencia` STRING, `unidade` STRING, `data` DATE, `valor` DECIMAL(18,6), `fonte` STRING e `extraido_em` TIMESTAMP. Não há desempate explícito para datas iguais; Silver já elimina chaves repetidas.

## `workspace.bcb_gold.economic_features`

Granularidade: uma linha por `mes`. Lacunas de publicação resultam em nulos, não em zeros.

| Campo | Tipo | Significado |
| --- | --- | --- |
| `mes` | DATE | Primeiro dia do mês. |
| `meta_selic` | DECIMAL(18,6) | Último valor mensal da SGS 432, em % a.a. |
| `ipca_mensal` | DECIMAL(18,6) | Último valor mensal da SGS 433, em % a.m. |
| `dolar_medio` | DECIMAL, escala derivada | Média mensal da SGS 1, em BRL/USD. |
| `selic_mensal` | DECIMAL(18,6) | Último valor mensal da SGS 4390, em % a.m. |
| `ipca_12_meses` | DECIMAL(18,6) | Último valor mensal da SGS 13522, em %. |
| `ano` | INT | Ano de `mes`. |
| `mes_numero` | INT | Número do mês, de 1 a 12. |

Os campos `meta_selic`, `ipca_mensal`, `selic_mensal` e `ipca_12_meses` são pivôs do `ultimo_valor`; `dolar_medio` vem de `valor_medio`. O mês corrente pode estar incompleto, sobretudo quando a série ainda não publicou o dado mensal.
