-- Execute cada consulta separadamente no Databricks SQL.
-- São verificações do estado atual; não substituem testes de integração automatizados.

-- Volumes atuais e reconciliação. Diferença pode incluir duplicidades removidas
-- ou estados de execuções distintas após falha entre escritas.
SELECT bronze.total AS registros_bronze,
       silver.total AS registros_silver,
       rejeitados.total AS registros_rejeitados,
       bronze.total - silver.total - rejeitados.total AS diferenca
FROM (SELECT COUNT(*) AS total FROM workspace.bcb_bronze.sgs_raw) bronze
CROSS JOIN (SELECT COUNT(*) AS total FROM workspace.bcb_silver.economic_indicators) silver
CROSS JOIN (SELECT COUNT(*) AS total FROM workspace.bcb_silver.data_quality) rejeitados;

-- Registros por tabela, inclusive Gold.
SELECT 'bronze.sgs_raw' AS tabela, COUNT(*) AS registros FROM workspace.bcb_bronze.sgs_raw
UNION ALL SELECT 'silver.economic_indicators', COUNT(*) FROM workspace.bcb_silver.economic_indicators
UNION ALL SELECT 'silver.data_quality', COUNT(*) FROM workspace.bcb_silver.data_quality
UNION ALL SELECT 'gold.monthly_indicators', COUNT(*) FROM workspace.bcb_gold.monthly_indicators
UNION ALL SELECT 'gold.latest_indicators', COUNT(*) FROM workspace.bcb_gold.latest_indicators
UNION ALL SELECT 'gold.economic_features', COUNT(*) FROM workspace.bcb_gold.economic_features;

-- Motivos de rejeição; zero rejeições gera conjunto vazio.
SELECT motivo_rejeicao, COUNT(*) AS registros
FROM workspace.bcb_silver.data_quality
GROUP BY motivo_rejeicao
ORDER BY registros DESC;

-- Unicidade Silver por série e data. Esperado: nenhum resultado.
SELECT codigo_serie, data, COUNT(*) AS ocorrencias
FROM workspace.bcb_silver.economic_indicators
GROUP BY codigo_serie, data
HAVING COUNT(*) > 1
ORDER BY ocorrencias DESC, codigo_serie, data;

-- Conflitos ainda presentes na Bronze, antes da regra que bloqueia a Silver.
SELECT codigo_serie, data_raw, COUNT(DISTINCT valor_raw) AS valores_distintos
FROM workspace.bcb_bronze.sgs_raw
GROUP BY codigo_serie, data_raw
HAVING COUNT(DISTINCT valor_raw) > 1
ORDER BY codigo_serie, data_raw;

-- Completude de campos essenciais na Silver, por série.
SELECT codigo_serie, indicador, COUNT(*) AS registros,
       SUM(CASE WHEN data IS NULL THEN 1 ELSE 0 END) AS datas_nulas,
       SUM(CASE WHEN valor IS NULL THEN 1 ELSE 0 END) AS valores_nulos,
       SUM(CASE WHEN extraido_em IS NULL THEN 1 ELSE 0 END) AS extracoes_nulas,
       SUM(CASE WHEN fonte IS NULL OR TRIM(fonte) = '' THEN 1 ELSE 0 END) AS fontes_ausentes
FROM workspace.bcb_silver.economic_indicators
GROUP BY codigo_serie, indicador
ORDER BY codigo_serie;

-- Cobertura mensal de features. NULL pode significar série ainda não publicada.
SELECT mes,
       CASE WHEN meta_selic IS NULL THEN 0 ELSE 1 END
       + CASE WHEN ipca_mensal IS NULL THEN 0 ELSE 1 END
       + CASE WHEN dolar_medio IS NULL THEN 0 ELSE 1 END
       + CASE WHEN selic_mensal IS NULL THEN 0 ELSE 1 END
       + CASE WHEN ipca_12_meses IS NULL THEN 0 ELSE 1 END AS series_disponiveis
FROM workspace.bcb_gold.economic_features
ORDER BY mes DESC;

-- Atualização por série: observe frequência e calendário de publicação antes de alertar atraso.
SELECT codigo_serie, indicador, frequencia,
       MAX(data) AS ultima_observacao,
       MAX(extraido_em) AS ultima_extracao,
       DATEDIFF(CURRENT_DATE(), MAX(data)) AS dias_desde_observacao
FROM workspace.bcb_silver.economic_indicators
GROUP BY codigo_serie, indicador, frequencia
ORDER BY codigo_serie;

-- Coerência de última observação Silver versus Gold. Esperado: nenhum resultado.
WITH silver_max AS (
    SELECT codigo_serie, MAX(data) AS data_maxima
    FROM workspace.bcb_silver.economic_indicators
    GROUP BY codigo_serie
)
SELECT silver_max.codigo_serie, silver_max.data_maxima, latest.data AS data_gold
FROM silver_max
LEFT JOIN workspace.bcb_gold.latest_indicators latest
    ON silver_max.codigo_serie = latest.codigo_serie
WHERE latest.data IS NULL OR latest.data <> silver_max.data_maxima;
