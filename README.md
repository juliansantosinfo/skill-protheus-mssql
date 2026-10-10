# protheus-mssql

Skill especializada para leitura, diagnóstico e orientação de manutenção do TOTVS Protheus em Microsoft SQL Server, para agentes que auxiliam desenvolvedores ADVPL/TLPP.

## Dependência
Instale a skill `mssql-database` ao lado desta. Ela mantém autenticação (`MSSQL_*`), ordem dos arquivos `.env`, seleção de `sqlcmd`/`pyodbc` e execução T-SQL. **Esta skill não inclui conexão própria e não armazena segredos.**

```text
.agents/skills/
  mssql-database/
    SKILL.md
    scripts/mssql_tool.py
    .env        # opcional; fallback conforme a skill base
  protheus-mssql/
    SKILL.md
    references/
    examples/
```

## Configuração
A prioridade do `.env` pertence à skill base: `--env-file` explícito > `.env` do diretório atual de execução > `.env` da raiz de `mssql-database`. Em ambiente com várias instâncias, prefira sempre `--env-file` explícito.

Exemplos:
```bash
python .agents/skills/mssql-database/scripts/mssql_tool.py --env-file ./conexoes/protheus-hml.env ping
python .agents/skills/mssql-database/scripts/mssql_tool.py --env-file ./conexoes/protheus-hml.env query --sql "SELECT DB_NAME() AS database_name"
```
O executor efetivo da skill base deve ser conferido com `--help` para argumentos que variem entre versões.

## Objetivos
- Encontrar schema e nome físico das tabelas associadas aos aliases lógicos.
- Validar colunas/tipos/índices reais no SQL Server e regras de filial/exclusão.
- Consultar dicionários SX quando estiverem acessíveis, ou orientar extração via AppServer/SIGACFG.
- Investigar registros e gerar SQL/TLPP/ADVPL apoiado em metadados reais.
- Orientar inclusão/atualização **pelo ERP**; por padrão, nunca gravar diretamente em tabelas Protheus via SQL.

## Uso típico com agente
> Use a skill protheus-mssql e a mssql-database no ambiente de homologação para descobrir as tabelas físicas SC5/SC6, validar campos e preparar uma consulta de pedidos por filial. Não faça alterações.

> Preciso cadastrar registros no Protheus. Investigue o dicionário e a rotina oficial e proponha uma implementação ADVPL/TLPP segura com validações, homologação e plano de reversão.

## Limitações
O pacote não identifica um ambiente real sozinho: exige credenciais, ferramentas do host e acesso ao SQL Server. Algumas SX não estarão disponíveis como tabelas SQL. Nenhuma escrita Protheus via SQL bruto está autorizada pela skill. Exemplos SQL são ponto de partida e devem ser ajustados/validados. Sem testes de integração contra ERP real.
