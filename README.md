# protheus-mssql

Skill autossuficiente e especializada para leitura, diagnóstico e execução de comandos SQL em bancos Microsoft SQL Server utilizados pelo TOTVS Protheus ERP, para agentes e desenvolvedores ADVPL/TLPP.

## Destaques
- **Zero Dependências Externas:** Utiliza 100% biblioteca padrão do Python 3 (`scripts/mssql_exec.py`). Sem necessidade de instalar `python-dotenv`, `sqlparse` ou `pyodbc`.
- **Suporte Nativo a Docker:** Conecta e executa comandos diretamente via containers Docker (ex.: `totvs_mssql`), sem exigir instalação de drivers ou `sqlcmd` no host.
- **Detecção Automática:** Suporta Docker, `sqlcmd` local do host ou drivers Python instalados.
- **Segurança Protheus Integrada:** Comandos de escrita por padrão rodam em modo PREVIEW (simulação transacional com ROLLBACK) e avisam sobre impacto em regras de negócio e dicionários do ERP.

## Estrutura da Skill
```text
skill-protheus-mssql/
  SKILL.md                       # Instruções principais da skill
  README.md                      # Documentação de uso
  .env.example                   # Exemplo de configuração de conexão
  scripts/
    mssql_exec.py                # Executor nativo e autossuficiente
  examples/
    01_context.sql               # Identificação do ambiente
    02_find_physical_tables.sql  # Descoberta de tabelas físicas
    03_columns.sql               # Inspeção de colunas e tipos
  references/
    DICTIONARY.md                # Diretrizes de catálogo de dicionário SX
    QUERY_RULES.md               # Regras de filial, D_E_L_E_T_ e joins
    WRITES.md                    # Boas práticas para manutenção de dados
    EXTENDING.md                 # Especializações futuras
  mssql-connections/             # Arquivos .env de conexões configuradas
  protheus-connections/          # Documentação contextual de ambientes mapeados
```

## Como Usar

### 1. Testar Conexão (Ping)
```bash
python scripts/mssql_exec.py ping
python scripts/mssql_exec.py ping --format table
```

### 2. Consultas de Leitura (Query)
```bash
# Query direta via SQL
python scripts/mssql_exec.py query --sql "SELECT TOP 10 name FROM sys.tables"

# Query a partir de arquivo .sql
python scripts/mssql_exec.py query --file examples/01_context.sql

# Saída formatada em tabela
python scripts/mssql_exec.py query --file examples/02_find_physical_tables.sql --format table
```

### 3. Execução de Comandos (Execute)
```bash
# Modo PREVIEW (simulação transacional com ROLLBACK automático)
python scripts/mssql_exec.py execute --sql "UPDATE SA1990 SET A1_NOME = 'Teste' WHERE A1_COD = '000001'"

# Modo PERSISTED (somente com confirmação explícita)
python scripts/mssql_exec.py execute --sql "UPDATE SA1990 SET A1_NOME = 'Teste' WHERE A1_COD = '000001'" --apply --ack confirmed
```

### 4. Conexões Específicas
```bash
python scripts/mssql_exec.py --env-file ./mssql-connections/totvs_mssql__protheus.env ping
python scripts/mssql_exec.py --container totvs_mssql ping
```

## Resolução de Configuração
O executor utiliza o arquivo `.env` localizado na raiz do projeto em execução (`cwd`):
1. Procura `.env` na raiz do projeto (`Path.cwd() / ".env"`) ou argumento explícito `--env-file`.
2. Se o `.env` não existir ou faltar qualquer uma das variáveis obrigatórias (`MSSQL_HOST`, `MSSQL_DATABASE`, `MSSQL_USER`, `MSSQL_PASSWORD`), o executor retorna erro imediato indicando o que falta, orientando a solicitar os dados ao usuário.
