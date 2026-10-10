# Padrões de consultas Protheus em SQL Server

## Primeiro o mapeamento
Alias lógico (ex.: `SA1`) **não** equivale necessariamente ao nome físico (`SA1010` é apenas exemplo). Resolver via SX2/`RetSqlName` em contexto correto do AppServer ou metadados confirmados pelo administrador. Valide schema, colunas, tipo e índices em `sys.*`.

## Filial, exclusão e RECNO
- Filial é contextual. `xFilial('SA1')` (exemplo ADVPL) leva em conta compartilhamento configurado. Em SQL puro não existe `xFilial()` por padrão: obtenha o valor em contexto, não suponha `C5_FILIAL = '01'` nem `LEFT` de um código qualquer.
- Condição típica para linhas ativas: `D_E_L_E_T_ = ' '` **quando a coluna existir**. Evite `TRIM` aplicado à coluna de filtro se prejudicar índices; atenção a CHAR com preenchimento de espaços.
- `R_E_C_N_O_` é identificador técnico, não chave de negócio global; nunca calcule `MAX(R_E_C_N_O_)+1` para inserir. `R_E_C_D_E_L_` não substitui o filtro lógico de ativo.
- Tabelas de itens (`SC6` etc.) geram cardinalidade 1:N; ao somar totais de cabeçalho, agregado por pedido pode duplicar.
- Datas Protheus em campos `CHAR(8)` usualmente seguem `AAAAMMDD`, mas confira o campo/tipo; não force conversões se dados incompletos ou espaços. Outros campos podem ser `DATE` ou conter valores legados.

## Modelo de consulta de vendas (NÃO executar sem adaptar)
```sql
SELECT TOP (50)
       SC5.C5_FILIAL,
       SC5.C5_NUM,
       SC5.C5_CLIENTE,
       SC5.C5_LOJACLI
FROM dbo.SC5010 AS SC5  -- EXEMPLO: confirmar nome/schema físicos
WHERE SC5.D_E_L_E_T_ = ' '
  AND SC5.C5_FILIAL = 'FILIAL_CONFIRMADA' -- substituir usando xFilial/SX2
ORDER BY SC5.C5_NUM DESC;
```

## Diagnóstico de desempenho
Analise plano de execução, predicados sargáveis, estatísticas e índices reais de SQL Server, sem criar/recriar índice diretamente em tabela Protheus sem processo autorizado. Avalie SQL montado em ADVPL/TLPP considerando `RetSqlName()`, `xFilial()`, `ChangeQuery()`, `TcGenQry()` e particularidades da instalação; não apresente funções de AppServer como se fossem funções T-SQL.
