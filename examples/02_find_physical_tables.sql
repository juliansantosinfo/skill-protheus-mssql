-- Somente nomes: confirme o sufixo correto no ambiente antes de consultar dados.
SELECT TOP (200) s.name AS schema_name, t.name AS table_name
FROM sys.tables AS t
INNER JOIN sys.schemas AS s ON s.schema_id = t.schema_id
WHERE t.name LIKE 'SA1%' OR t.name LIKE 'SX2%' OR t.name LIKE 'SX3%'
   OR t.name LIKE 'SC5%' OR t.name LIKE 'SC6%' OR t.name LIKE 'SIX%'
ORDER BY t.name;
