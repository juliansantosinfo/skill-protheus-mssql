---
name: protheus-mssql
description: Especialista em leitura e diagnóstico de bancos Microsoft SQL Server utilizados pelo TOTVS Protheus para desenvolvedores ADVPL/TLPP; interpreta SX2/SX3/SIX/SX5/SX6/SX7/SX9 quando acessíveis, localiza tabelas físicas e filialização, gera T-SQL/ADVPL e orienta escritas exclusivamente por caminhos seguros do ERP. Depende da skill mssql-database.
compatibility: Linux, Windows e macOS; requer mssql-database para conexão SQL Server. Acesso ao dicionário ativo via AppServer/Configurador pode exigir ferramentas adicionais.
---

# Protheus MSSQL — especialização da skill mssql-database

## Ativação
Ative em demandas envolvendo TOTVS Protheus + SQL Server: descoberta de tabelas/campos, dicionário SX, validação de joins, investigação de dados, suporte a ADVPL/TLPP, elaboração de SQL, identificação de impacto de correções e inclusão/atualização de registros. Esta skill **não contém credenciais nem outro executor SQL**: delega transporte, validação de conexão, DQL e eventual SQL autorizado à skill `mssql-database`. Se a skill base não estiver instalada/acessível, peça sua instalação/configuração; não improvise conexão nem credenciais.

## Conduta obrigatória
1. Descubra qual instância, banco, empresa/grupo, filial, ambiente (dev/hml/prod), objetivo de negócio e autorização estão em escopo. Use `--env-file` explícito se houver múltiplos bancos. Execute `ping` e identificação somente leitura antes de qualquer outra ação. Se o escopo não estiver inequívoco **pergunte**. Não escolha produção por conveniência.
2. Confira `references/DICTIONARY.md`, `references/QUERY_RULES.md` e `references/WRITES.md` antes de sugerir alterações. **Não suponha** que todas as SX estão no SQL Server ou que seus nomes físicos são `SX2010`, `SX3010` etc. Descubra objetos realmente existentes em `sys.tables`; o dicionário ativo pode ser mantido em arquivos/repositório e acessado pelo AppServer ou SIGACFG.
3. Para toda tabela de negócio: descubra nome físico real, schema, colunas existentes e tipos, índices, filtros de filial e exclusão lógica. Use `R_E_C_N_O_`, `R_E_C_D_E_L_`, `D_E_L_E_T_` apenas se existirem e no papel correto. `D_E_L_E_T_ = ' '` normalmente indica registro ativo; não assuma isto em tabelas fora do padrão. Nunca adivinhe a empresa/sufixo (`SA1010` é só exemplo).
4. Respeite compartilhamento da SX2 (por empresa/unidade), regras `xFilial(alias)`, filial com tamanho/configuração específicos, empresas e grupos; **não** traduza arbitrariamente `xFilial()` em `substring`, nem transforme filial compartilhada em filial corrente. Quando esses metadados não estiverem disponíveis, peça confirmação e rotule a consulta como provisória.
5. Toda leitura deve ser delimitada: colunas explícitas, `TOP`, filtros pertinentes, preferencialmente parâmetros e amostra mascarada quando dados pessoais/financeiros. Não exporte bases indiscriminadamente. Para `JOIN`, valide cardinalidade e chaves reais; evite duplicar linhas em ligações 1:N.
6. **Regra prioritária para gravação:** por padrão NÃO execute `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `TRUNCATE` ou DDL diretamente em tabelas de negócio/dicionário do Protheus pelo SQL Server. Proponha implementação via regras e APIs do ERP (AdvPL/TLPP, MVC, MsExecAuto quando cabível, RecLock/MSUnlock, serviços oficiais) e homologação. SQL direto pode ignorar validações, gatilhos da aplicação, numeração, logs, integrações, relacionamentos e controles de concorrência. Em SX*, SXE/SXF, índices e estrutura física, a alteração via SQL é **bloqueada** por esta skill; usar mecanismos suportados do Configurador, atualização de dicionário ou administração homologada.
7. Exceção para SQL de escrita em tabela **comprovadamente externa ao Protheus** ou staging segregado: herda integralmente controles da skill `mssql-database` (plano, impacto, consulta prévia, rollback, aprovação explícita para instrução/destino). Para tabelas de negócio Protheus, mesmo com pedido de escrita direta, explique riscos e peça autorização para desenhar a solução via ERP em vez de executar SQL bruto.
8. Em dúvidas de campo, máscara, tipo, enumeração, relação, vínculo de filial, regra de negócio ou consequência da operação, questione o usuário antes de propor ou executar mudanças. Nunca use documentação genérica como substituto à conferência da versão/ambiente ativo.
9. Nunca executar SQL apenas porque o usuário pediu para **escrever um exemplo**. Diferencie consulta realmente executada, SQL sugerido, inferência e hipótese. Registre objeto físico, filtros de empresa/filial/exclusão, resultados limitados, riscos e pendências.

## Fluxo de leitura
1. Conecte usando `mssql-database/scripts/mssql_tool.py`, preservando prioridade `.env`: `--env-file` > `.env` do projeto/cwd > `.env` da skill base. Esta skill não sobrescreve essa prioridade.
2. Descubra `DB_NAME()`, `@@SERVERNAME`, `SYSTEM_USER`, `sys.tables`, `sys.columns`, `sys.indexes` (scripts em `examples/`).
3. Se o usuário indicar alias (`SA1`, `SB1`, `SC5`, `SC6`, `SF2`, `SE1`, etc.), encontre tabelas físicas candidatas e valide pelo ambiente/SX2, em vez de escolher o primeiro prefixo.
4. Se SX2/SX3/SIX/SX6 etc. estiverem efetivamente expostas no SQL, confirme schema/estrutura e leia metadados pertinentes. Se não, indique consulta via SIGACFG, APIs/framework do AppServer (`GetSX3Cache`, `TamSX3`, `RetSqlName`, `xFilial` quando apropriado) ou exportação autorizada do dicionário ativo. Nomes/funções variam conforme necessidade e versão; verificar documentação e comportamento.
5. Construa consulta segura, confirme filtros e cardinalidade, rode `query` com `TOP` e faça leitura crítica do resultado.
6. Se o pedido incluir escrita, escolha primeiro o fluxo ADVPL/TLPP suportado e consulte `references/WRITES.md`.

## Exemplos de uso da skill base
```bash
python .agents/skills/mssql-database/scripts/mssql_tool.py --env-file ./conexoes/protheus-hml.env ping
python .agents/skills/mssql-database/scripts/mssql_tool.py --env-file ./conexoes/protheus-hml.env query --file .agents/skills/protheus-mssql/examples/01_context.sql
python .agents/skills/mssql-database/scripts/mssql_tool.py --env-file ./conexoes/protheus-hml.env query --file .agents/skills/protheus-mssql/examples/02_find_physical_tables.sql
```
Exemplos ilustrativos: adapte caminhos conforme plataforma e projeto. Se o executor não suportar `query --file`, confira `--help` e use `--sql` ou o mecanismo adequado da skill base; não force uma sintaxe não suportada.

## Integração com skills por processo
Uma futura skill `protheus-vendas`, `protheus-financeiro`, `protheus-estoque` etc. deve declarar dependência desta skill e registrar aliases, campos reais, processos, cardinalidades, filtros por filial e interfaces oficiais de escrita. Não substituir a descoberta do ambiente por valores fixos.
