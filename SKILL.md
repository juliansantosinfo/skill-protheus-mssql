---
name: protheus-mssql
description: Use when querying, diagnosing, or executing SQL commands on Microsoft SQL Server for TOTVS Protheus ERP, inspecting SX dictionary tables, physical table mapping, or generating queries.
---

# Protheus MSSQL

Skill direta para execução de consultas e comandos SQL em Microsoft SQL Server para TOTVS Protheus ERP.

## Fluxo de Execução Imediata
* **Vá direto à execução:** Não execute `ping` prévio nem leia arquivos de referência antes de responder. Execute o comando SQL solicitado imediatamente.
* **Arquivo `.env` Mandatório:** O executor utiliza exclusivamente o `.env` na raiz do projeto (`cwd`).
  * Se o comando retornar erro de `.env` ausente ou incompleto (`MSSQL_HOST`, `MSSQL_DATABASE`, `MSSQL_USER`, `MSSQL_PASSWORD`), **pergunte imediatamente os valores ao usuário** e crie/atualize o `.env` na raiz com a confirmação dele.
* **Zero dependências extras:** O executor (`scripts/mssql_exec.py`) roda em Python puro e detecta automaticamente containers Docker locais (ex: `totvs_mssql`) ou `sqlcmd` do host.

## Regras Protheus Essenciais
1. **Exclusão Lógica:** Sempre inclua `WHERE D_E_L_E_T_ = ' '` para tabelas de negócio ativas.
2. **Filial (`xFilial` / `SX2`):** Tabelas compartilhadas usam espaços (`'  '`); exclusivas usam o código da filial (ex: `'01'`). Nunca cruze campos `_FILIAL` de tabelas com compartilhamento diferente.
3. **Projeção:** Projete colunas explícitas (evite `SELECT *`). O executor limita o resultado por padrão a 10 linhas para economizar tokens.

## Comandos do Executor

```bash
# Consultas de leitura (DQL) - limite padrão de 10 linhas
python scripts/mssql_exec.py query --sql "SELECT TOP 10 A1_COD, A1_NOME FROM SA1990 WHERE D_E_L_E_T_ = ' '"

# Consulta com limite personalizado ou arquivo .sql
python scripts/mssql_exec.py query --file examples/01_context.sql
python scripts/mssql_exec.py query --sql "SELECT name FROM sys.tables" --limit 50

# Execução de comandos (DML/DDL)
# 1. Simulação segura (PREVIEW com ROLLBACK)
python scripts/mssql_exec.py execute --sql "UPDATE SA1990 SET A1_NOME = 'Teste' WHERE A1_COD = '000001'"

# 2. Persistência real (após aprovação humana inequívoca)
python scripts/mssql_exec.py execute --sql "UPDATE SA1990 SET A1_NOME = 'Teste' WHERE A1_COD = '000001'" --apply --ack confirmed
```
