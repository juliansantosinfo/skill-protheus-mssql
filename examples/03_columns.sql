-- Inspecione as colunas da tabela física confirmada em sys.tables.
-- Substitua somente o literal 'SA1010' pelo nome confirmado (sem concatenar SQL de origem não confiável).
SELECT s.name AS schema_name, t.name AS table_name, c.column_id,
       c.name AS column_name, ty.name AS sql_type, c.max_length, c.is_nullable
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id = t.schema_id
JOIN sys.columns c ON c.object_id = t.object_id
JOIN sys.types ty ON ty.user_type_id = c.user_type_id
WHERE t.name = 'SA1010'
ORDER BY c.column_id;
