# Contexto do Ambiente TOTVS Protheus: totvs_mssql__protheus

## 1. Identificação do Ambiente

- **Nome Lógico:** TOTVS Protheus 12.1.2510 (Ambiente Local Docker)
- **Instância SQL Server:** `totvs_mssql` (Container Docker / Server Name: `6b2a87cae9ba`)
- **Database Ativo:** `protheus`
- **Versão do SGBD:** Microsoft SQL Server 2019 (RTM-CU32-GDR) - 15.0.4445.1 (X64) Developer Edition on Linux (Ubuntu 20.04.6 LTS)
- **Collation do Database:** `Latin1_General_BIN` (Padrão mandatório TOTVS Protheus)
- **Nível de Compatibilidade:** 150 (SQL Server 2019)
- **Schemas Identificados:**
  - `dbo`: 574 tabelas (Tabelas de negócio, dicionários SX, cadastros de sistema)
  - `HangFire`: 11 tabelas (Fila e controle de tarefas em background - Smart View / Relatórios)
- **Data da Análise:** 2026-10-10

## 2. Referência de Conexão

- **Arquivo `.env` Correspondente:** `./mssql-connections/totvs_mssql__protheus.env`
- **Host / Porta:** `127.0.0.1:1433`
- **Usuário Conectado:** `sa` (Funções: `sysadmin`, `db_owner`)
- **Segurança:** Credenciais protegidas por política de segurança. Não expor senhas em artefatos ou logs.
- **Observação de Transporte:** O serviço SQL Server executa em container Docker (`totvs_mssql`). A execução via `scripts/mssql_exec.py` conecta nativamente via Docker ou `sqlcmd` com certificado confiado (`-C`).

## 3. Evidências que Confirmam o Ambiente Protheus

1. **Collation Binário Obrigatório:** Database configurado com `Latin1_General_BIN`.
2. **Metadados de Release do ERP em `dbo.SYSTEM_INFO`:**
   - `DIC`: `12.1.2510`
   - `SIGAMAT`: `12.1.2510`
   - `MENU`: `12.1.2510`
   - `USER_VERSION`: `12.1.2510`
   - `PROFILEINDB`: `12.1.2510`
3. **Parâmetros Oficiais em `dbo.SX6990`:**
   - `MV_ESTADO` = `'SP'`
   - `MV_PAISLOC` = `'BRA'`
   - `MV_MOEDA1` = `'REAL'`
4. **Campos Técnicos Padrão em Todas as Tabelas de Negócio:**
   - `R_E_C_N_O_` (`bigint`): Identificador físico único / Chave primária clustered (`*_PK`).
   - `R_E_C_D_E_L_` (`bigint`): Controle de exclusão lógica do DBAccess (`0` para registros ativos, `= R_E_C_N_O_` para excluídos).
   - `D_E_L_E_T_` (`varchar(1)`): Flag de exclusão lógica (`' '` para registros ativos, `'*'` para registros excluídos).
5. **Índices Físicos DBAccess:**
   - Índice Clustered PK: `TABELA_PK` sobre `R_E_C_N_O_`.
   - Índice Único DBAccess: `TABELA_UNQ` composto pelas colunas de chave de negócio + `R_E_C_D_E_L_`.
   - Índices Não-Clustered: `TABELA1`, `TABELA2`, etc. correspondentes às ordens lógicas do SIX.
6. **Presença Física dos Dicionários de Dados SX e SIX:** Tabelas com sufixo `990` totalmente populadas no SQL Server.
7. **Tabelas de Negócio Clássicas Identificadas:** `SA1990` (Clientes), `SA2990` (Fornecedores), `SB1990` (Produtos), `SC5990` (Pedidos Venda), `SC6990` (Itens Pedido), `SD1990` (Itens NF Entrada), `SD2990` (Itens NF Saída), `SE1990` (Contas a Receber), `SE2990` (Contas a Pagar).

## 4. Grupos de Empresas e Filiais Identificados

Estrutura obtida via `dbo.SYS_COMPANY` e `dbo.SYS_COMPANY_CFG`:

- **Empresa / Grupo:** `99` (Nome: `TESTE`)
- **Filial:** `01` (Nome: `MATRIZ`)
- **Tamanho Real do Campo Filial:** `2` posições (`M0_SIZEFIL = 2.0`, Layout `FF`)
- **Status:** Ativo
- **Observação sobre Sufixos Físicos:** As tabelas do Protheus neste ambiente utilizam o sufixo `990` (formado por Empresa `99` + Unidade Física `0`).

## 5. Regras de Compartilhamento Confirmadas (SX2 / xFilial)

Verificação realizada diretamente em `dbo.SX2990` e confirmada nos dados físicos:

| Alias | Tabela Física | Descrição | Modo Filial (`X2_MODO`) | Modo Empresa (`X2_MODOEMP`) | Comportamento `xFilial()` | Valor Armazenado no Campo `_FILIAL` |
|---|---|---|:---:|:---:|---|---|
| **SA1** | `SA1990` | Clientes | **C** (Compartilhado) | **E** (Exclusivo) | Retorna string vazia (`""` ou `'  '`) | Dois espaços em branco (`'  '`) |
| **SA2** | `SA2990` | Fornecedores | **C** (Compartilhado) | **E** (Exclusivo) | Retorna string vazia (`""` ou `'  '`) | Dois espaços em branco (`'  '`) |
| **SB1** | `SB1990` | Produtos | **C** (Compartilhado) | **E** (Exclusivo) | Retorna string vazia (`""` ou `'  '`) | Dois espaços em branco (`'  '`) |
| **SC5** | `SC5990` | Pedidos de Venda | **E** (Exclusivo) | **E** (Exclusivo) | Retorna filial corrente (`'01'`) | `'01'` |
| **SC6** | `SC6990` | Itens de Pedido | **E** (Exclusivo) | **E** (Exclusivo) | Retorna filial corrente (`'01'`) | `'01'` |
| **SD1** | `SD1990` | Itens NF Entrada | **E** (Exclusivo) | **E** (Exclusivo) | Retorna filial corrente (`'01'`) | `'01'` |
| **SD2** | `SD2990` | Itens NF Saída | **E** (Exclusivo) | **E** (Exclusivo) | Retorna filial corrente (`'01'`) | `'01'` |
| **SE1** | `SE1990` | Contas a Receber | **E** (Exclusivo) | **E** (Exclusivo) | Retorna filial corrente (`'01'`) | `'01'` |
| **SE2** | `SE2990` | Contas a Pagar | **E** (Exclusivo) | **E** (Exclusivo) | Retorna filial corrente (`'01'`) | `'01'` |

> [!IMPORTANT]
> **Atenção Mandatória para Joins em T-SQL:**
> - Nunca realizar join de filial entre tabelas com modos de compartilhamento divergentes!
> - Exemplo de Erro Crítico: `SC5.C5_FILIAL = SA1.A1_FILIAL` **não retornará registros**, pois `C5_FILIAL = '01'` e `A1_FILIAL = '  '`.
> - Forma Correta: `WHERE SC5.C5_FILIAL = '01' AND SA1.A1_FILIAL = '  ' AND SA1.A1_COD = SC5.C5_CLIENTE AND SA1.A1_LOJA = SC5.C5_LOJACLI`.

## 6. Disponibilidade dos Dicionários SX no SQL Server

Todos os principais dicionários estão residentes como tabelas físicas no SQL Server com sufixo `990`:

| Dicionário | Tabela Física | Registros Ativos | Finalidade | Campos Principais de Consulta |
|---|---|:---:|---|---|
| **SX1** | `dbo.SX1990` | 58.055 | Perguntas e Parâmetros de Rotinas | `X1_GRUPO`, `X1_ORDEM`, `X1_PERGUNT`, `X1_VAR01`, `X1_TIPO` |
| **SX2** | `dbo.SX2990` | 10.820 | Cadastro de Tabelas do ERP | `X2_CHAVE`, `X2_ARQUIVO`, `X2_NOME`, `X2_MODO`, `X2_MODOEMP`, `X2_UNICO` |
| **SX3** | `dbo.SX3990` | 177.418 | Cadastro e Dicionário de Campos | `X3_ARQUIVO`, `X3_CAMPO`, `X3_TIPO`, `X3_TAMANHO`, `X3_DECIMAL`, `X3_TITULO`, `X3_PROPRI` |
| **SX5** | `dbo.SX5990` | 11.764 | Tabelas Genéricas Protheus | `X5_TABELA`, `X5_CHAVE`, `X5_DESCRI` |
| **SX6** | `dbo.SX6990` | 12.117 | Parâmetros Gerais MV_* | `X6_VAR`, `X6_TIPO`, `X6_DESCRIC`, `X6_CONTEUD` |
| **SX7** | `dbo.SX7990` | 16.692 | Gatilhos de Campos (Triggers de Aplicação) | `X7_CAMPO`, `X7_SEQUENC`, `X7_REGRA`, `X7_CDOMIN` |
| **SX9** | `dbo.SX9990` | 26.300 | Relacionamentos entre Entidades | `X9_DOM`, `X9_CDOM`, `X9_EXPDOM`, `X9_EXPCDOM` |
| **SIX** | `dbo.SIX990` | 25.472 | Índices Lógicos do ERP | `INDICE`, `ORDEM`, `CHAVE`, `DESCRICAO`, `NICKNAME` |
| **SXA** | `dbo.SXA990` | 1.838 | Pastas e Agrupamentos Visuais de Tela | `XA_ALIAS`, `XA_ORDEM`, `XA_DESCRIC` |
| **SXB** | `dbo.SXB990` | 56.319 | Consultas Padrão (Lookups F3) | `XB_ALIAS`, `XB_TIPO`, `XB_COLUNA`, `XB_DESCRI` |
| **SXE/SXF** | *(Inexistentes)* | 0 | Numeração Sequencial de Documentos | Gerenciado em memória / DBAccess / AppServer (sem tabela SQL) |

## 7. Estruturas Customizadas Identificadas

- **Campos Customizados (`X3_PROPRI = 'U'`):** 46 campos customizados registrados no `SX3990`, incluindo:
  - `SB1`: `B1_XCORIG`, `B1_XDCORIG`, `B1_XDMARCA`, `B1_XMARCA`, `B1_XREFERE`
  - `SC5`: `C5_XETAPA`, `C5_XETPERR`, `C5_XLIBPRZ`, `C5_XLOGINT`, `C5_ZZCANCE`, `C5_ZZDESMC`, `C5_ZZMTCAN`
  - `SC6`: `C6_ZZITCSV`
  - `EE8`: `EE8_ZZITCS`
- **Tabelas Customizadas (Z):**
  - `dbo.ZM1990` (Integrações / Query RPO)
  - `dbo.ZX1990`, `dbo.ZX2990`, `dbo.ZX3990`, `dbo.ZX4990` (Gestão de Marcas / Fabricantes)

## 8. Diretrizes de Operação para Agentes de IA

### Operações de Leitura (DQL)
1. **Filtro Mandatório de Exclusão:** Incluir sempre `AND D_E_L_E_T_ = ' '`.
2. **Projeção Explícita e Limite:** Utilizar sempre colunas explícitas (evitar `SELECT *`) e cláusula `TOP (N)`.
3. **Resolução de Filial:** Utilizar a regra de compartilhamento obtida em `SX2990` / `xFilial`. Não arbitrar `'01'`.
4. **Relacionamentos:** Lembrar que os relacionamentos de negócio Protheus são lógicos (`SX9990`); não existem chaves estrangeiras físicas (`sys.foreign_keys`) nas tabelas padrão do ERP.

### Operações de Escrita (DML / DDL)
> [!CAUTION]
> **Proibição Estrita de SQL Direto em Tabelas Protheus:**
> - Nunca executar `INSERT`, `UPDATE`, `DELETE` ou `TRUNCATE` diretamente via SQL em tabelas de negócio (`SA*`, `SB*`, `SC*`, `SD*`, `SE*`, etc.) ou dicionários (`SX*`, `SIX`).
> - A escrita direta contorna validações do `SX3`, integridade do MVC, gatilhos de aplicação (`SX7`), pontos de entrada (`PARAMIXB`), controle de concorrência (`RecLock`), auditoria (`SYS_AUDIT`) e o mecanismo de numeração sequencial.
> - Toda escrita deve ser direcionada para ADVPL/TLPP via rotinas oficiais (`MsExecAuto`, Classes de Modelo MVC, `FWFormModel`, `RecLock()` ou APIs REST TTALK).
> - Tabelas comprovadamente externas ou staging (ex.: tabelas auxiliares fora do padrão Protheus) exigem aprovação humana explícita prévia e transação com simulação de rollback via `scripts/mssql_exec.py execute`.

## 9. Limitações e Pendências

1. **Numeração Automática (SXE/SXF):** Não reside em tabelas SQL Server. Intervenções em numeração dependem do AppServer ou rotinas padrão do ERP.
2. **Configuração de Execução:** O ambiente executa dentro do container `totvs_mssql`. O executor `scripts/mssql_exec.py` gerencia automaticamente a execução direta via Docker sem requerer drivers no host.
3. **Escopo de Dados:** Ambiente de testes/desenvolvimento montado na Empresa `99` e Filial `01`.
