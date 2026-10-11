# Inserção e manutenção de dados em Protheus

## Política central
SQL Server é armazenamento do ERP, não camada de regra de negócio. Alterar tabelas Protheus diretamente com INSERT/UPDATE/DELETE/MERGE/DDL pode contornar validações SX3, regras MVC, pontos de entrada, gatilhos ADVPL, controle de numeração SXE/SXF, locks, integridade lógica, rastreabilidade, cálculo fiscal/financeiro e integração EAI. Por esse motivo, comandos de alteração em tabelas de negócio e dicionário devem ser preferencialmente implementados via rotinas oficiais do Protheus. Quando a execução direta em banco for indispensável ou se tratar de tabelas externas/staging, deve ser utilizado o modo de simulação transacional (`execute` PREVIEW com rollback) antes de qualquer persistência autorizada (`--apply --ack confirmed`).

## Fluxo para pedidos de inclusão/alteração
1. Perguntar qual operação/módulo, ambiente, empresa, filial, alias, chave, origem do dado e resultado esperado. Confirmar se é intervenção excepcional ou funcionalidade definitiva.
2. Verificar dicionário ativo, campos obrigatórios/validações, chaves, relacionamentos, eventos e rotina padrão responsável.
3. Preferir APIs e rotinas oficiais, MVC, `MsExecAuto` **quando a rotina suportar**, ou ADVPL/TLPP com `RecLock()`/`MSUnlock()` em **customização que respeite o contrato do módulo**; RecLock isoladamente não implementa regras de negócio. Consultar rotina/PE e versão antes de gerar código executável.
4. Preparar proposta/testes para homologação; incluir transações `Begin Transaction`/`End Transaction` e rollback (`DisarmTransaction()` quando aplicável) sob validação da release e contratos de execução; prever concorrência, logs e idempotência.
5. Ao usuário pedir SQL bruto, apresentar SELECT de diagnóstico, plano e riscos. Se a execução for aprovada, utilizar `scripts/mssql_exec.py execute` em modo PREVIEW para validação e, após aprovação explícita, `--apply --ack confirmed`.
6. Nunca usar `MAX(R_E_C_N_O_)+1`, atualizar `D_E_L_E_T_` para 'reativar' dados ou ajustar SXE/SXF diretamente como substituto das rotinas suportadas.

## Perguntas obrigatórias quando houver incerteza
- Qual empresa/filial e ambiente? Existe outro banco parecido?
- O alias/campo foi confirmado no dicionário ativo? Há tabela física identificada?
- É somente leitura, elaboração de código ADVPL/TLPP ou execução que altera dados?
- Existe rotina padrão/API para a operação? Há impactos fiscal, financeiro, estoque, lotes, seriais e EAI?
- Há janela de homologação, backup e plano de reversão? Quem aprova?
