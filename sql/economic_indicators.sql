-- Execute cada consulta separadamente no editor Databricks SQL.
-- As tabelas refletem o último Full Refresh bem-sucedido de cada etapa.

-- Últimos indicadores: cartão com valor, unidade e data de referência.
SELECT codigo_serie, indicador, data, valor, unidade, frequencia, extraido_em
FROM workspace.bcb_gold.latest_indicators
ORDER BY indicador;

-- Evolução mensal: filtre por codigo_serie ao criar o gráfico para não misturar unidades.
SELECT mes, codigo_serie, indicador, unidade, frequencia,
       valor_medio, ultimo_valor, observacoes, ultima_observacao
FROM workspace.bcb_gold.monthly_indicators
ORDER BY mes, codigo_serie;

-- Dólar: média das observações diárias, não cotação de fechamento.
SELECT mes, dolar_medio
FROM workspace.bcb_gold.economic_features
WHERE dolar_medio IS NOT NULL
ORDER BY mes;

-- Taxas mensais comparáveis em % a.m.; a disponibilidade pode diferir por mês.
SELECT mes, ipca_mensal, selic_mensal
FROM workspace.bcb_gold.economic_features
WHERE ipca_mensal IS NOT NULL OR selic_mensal IS NOT NULL
ORDER BY mes;

-- Base mensal completa. Meses sem publicação de alguma série mantêm NULL.
SELECT mes, ano, mes_numero, meta_selic, ipca_mensal,
       dolar_medio, selic_mensal, ipca_12_meses
FROM workspace.bcb_gold.economic_features
ORDER BY mes DESC;

-- Comparação de último valor por série entre meses consecutivos.
WITH evolucao AS (
    SELECT mes, codigo_serie, indicador, unidade, ultimo_valor,
           LAG(ultimo_valor) OVER (PARTITION BY codigo_serie ORDER BY mes) AS valor_mes_anterior
    FROM workspace.bcb_gold.monthly_indicators
)
SELECT mes, codigo_serie, indicador, unidade, ultimo_valor,
       valor_mes_anterior,
       ultimo_valor - valor_mes_anterior AS variacao_absoluta
FROM evolucao
WHERE valor_mes_anterior IS NOT NULL
ORDER BY mes DESC, codigo_serie;
