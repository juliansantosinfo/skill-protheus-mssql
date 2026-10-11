---
name: protheus-mssql
description: Use when querying, diagnosing, or executing SQL commands on Microsoft SQL Server for TOTVS Protheus ERP, inspecting SX dictionary tables, physical table mapping, or generating queries.
---

# Protheus MSSQL

Skill autossuficiente para leitura, diagnóstico e execução de comandos SQL em bancos Microsoft SQL Server utilizados pelo TOTVS Protheus ERP (desenvolvimento ADVPL/TLPP e sustentação).

## Visão Geral
* **Zero dependências externas:** utiliza exclusivamente a biblioteca padrão do Python 3 (`scripts/mssql_exec.py`). Não requer instalação de `python-dotenv`, `sqlparse` ou `pyodbc`.
* **Multi-backend automático:** detecta se o SQL Server roda em container Docker (ex.: `totvs_mssql` local), utiliza o `sqlcmd` do host ou fallback para drivers Python se disponíveis.
* **Segurança e proteção de dados Protheus:** execuções de comandos de escrita por padrão rodam em modo **PREVIEW com ROLLBACK transacional**, exigindo confirmação explícita (`--apply --ack confirmed`) para persistência.

## Conduta Obrigatória
1. **Identificação inicial:** Antes de qualquer alteração, execute `ping` para validar banco, servidor, usuário e versão. Identifique se o ambiente é desenvolvimento, homologação ou produção. Se o escopo for ambíguo, **pergunte**.
2. **Mapeamento lógico vs. físico:** Não assuma nomes fixos (`SA1010`, `SX2010`). Descubra os objetos reais em `sys.tables`. No Protheus, o sufixo varia por empresa e unidade (ex.: `990` para Empresa `99`).
3. **Padrões Protheus Mandatórios:**
   - **Exclusão lógica:** Sempre incluir `D_E_L_E_T_ = ' '` nas consultas de tabelas de negócio ativas.
   - **Filial:** Respeite a regra de compartilhamento da tabela (`SX2` / `xFilial`). Tabelas compartilhadas usam espaços em branco (`'  '`), enquanto tabelas exclusivas usam o código da filial (ex.: `'01'`). Nunca faça joins diretos de campos `_FILIAL` entre tabelas com modos de compartilhamento distintos.
   - **Campos técnicos:** `R_E_C_N_O_` é identificador técnico sequencial; nunca use `MAX(R_E_C_N_O_) + 1` para inserções manuais.
4. **Delimitação de leituras:** Toda consulta DQL deve projetar colunas explícitas (evite `SELECT *`) e utilizar `TOP (N)` para evitar sobrecarga de memória e bloqueios (locks).
5. **Execução de comandos de escrita (DML/DDL):**
   - Em tabelas de negócio do Protheus (`SA*`, `SB*`, `SC*`, `SD*`, `SE*`) ou dicionários (`SX*`, `SIX`), a gravação direta via SQL ignora validações de dicionário (`SX3`), integridade MVC, triggers de aplicação (`SX7`), pontos de entrada (`PARAMIXB`) e numeração (`SXE/SXF`). Sempre que possível, oriente a gravação via ERP (AdvPL/TLPP com `MsExecAuto`, Classes MVC ou `RecLock`).
   - Caso a execução de comandos SQL seja necessária e autorizada pelo usuário, o executor oferece simulação prévia com rollback automático. Somente persista alterações após aprovação inequívoca.

## Interface do Executor (`scripts/mssql_exec.py`)

O executor é independente e resolve credenciais via `--env-file`, `.env` do diretório atual ou `mssql-connections/*.env`:

```bash
# 1. Testar conectividade e identificar ambiente
python scripts/mssql_exec.py ping
python scripts/mssql_exec.py ping --format table

# 2. Executar consultas de leitura (SELECT)
python scripts/mssql_exec.py query --sql "SELECT TOP 10 name FROM sys.tables"
python scripts/mssql_exec.py query --file examples/01_context.sql
python scripts/mssql_exec.py query --file examples/02_find_physical_tables.sql --format table

# 3. Execução de comandos com proteção transacional
# Modo PREVIEW (padrão seguro: executa dentro de transação e faz ROLLBACK)
python scripts/mssql_exec.py execute --sql "UPDATE SA1990 SET A1_NOME = 'Teste' WHERE A1_COD = '000001'"

# Modo PERSISTED (somente após aprovação explícita do usuário)
python scripts/mssql_exec.py execute --sql "UPDATE SA1990 SET A1_NOME = 'Teste' WHERE A1_COD = '000001'" --apply --ack confirmed

# 4. Conexão com arquivo específico ou container específico
python scripts/mssql_exec.py --env-file ./mssql-connections/totvs_mssql__protheus.env ping
python scripts/mssql_exec.py --container totvs_mssql ping
```

## Opções do Executor
* `--env-file`: Caminho explícito para arquivo `.env` de conexão.
* `--client`: Forçar backend (`auto`, `docker`, `sqlcmd`, `python`).
* `--container`: Nome do container Docker do SQL Server (padrão detecta automaticamente, ex: `totvs_mssql`).
* `--format`: Formato de saída (`json` [padrão para agentes], `table` [tabular legível], `raw` [saída bruta]).
* `--limit`: Limite de linhas retornadas em queries (padrão 100).
