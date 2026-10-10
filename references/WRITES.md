# Inserção e manutenção de dados em Protheus

## Política central
SQL Server é armazenamento do ERP, não camada de regra de negócio. Alterar tabelas Protheus diretamente com INSERT/UPDATE/DELETE/MERGE/DDL pode contornar validações SX3, regras MVC, pontos de entrada, gatilhos ADVPL, controle de numeração SXE/SXF, locks, integridade lógica, rastreabilidade, cálculo fiscal/financeiro e integração EAI. Portanto a skill **não executa SQL de escrita nessas tabelas**. Esta é uma restrição deliberada da especialização, mesmo que a skill master aceite escrita SQL genericamente.

## Fluxo para pedidos de inclusão/alteração
1. Perguntar qual operação/módulo, ambiente, empresa, filial, alias, chave, origem do dado e resultado esperado. Confirmar se é intervenção excepcional ou funcionalidade definitiva.
2. Verificar dicionário ativo, campos obrigatórios/validações, chaves, relacionamentos, eventos e rotina padrão responsável.
3. Preferir APIs e rotinas oficiais, MVC, `MsExecAuto` **quando a rotina suportar**, ou ADVPL/TLPP com `RecLock()`/`MSUnlock()` em **customização que respeite o contrato do módulo**; RecLock isoladamente não implementa regras de negócio. Consultar rotina/PE e versão antes de gerar código executável.
4. Preparar proposta/testes para homologação; incluir transações `Begin Transaction`/`End Transaction` e rollback (`DisarmTransaction()` quando aplicável) sob validação da release e contratos de execução; prever concorrência, logs e idempotência.
5. Ao usuário pedir SQL bruto, apresentar SELECT de diagnóstico, plano e riscos; não executar em tabela de negócio. Se a tabela for **externa/staging comprovada**, delegar à skill master com aprovação explícita, simulação transacional e confirmações.
6. Never usar `MAX(R_E_C_N_O_)+1`, atualizar `D_E_L_E_T_` para 'reativar' dados ou ajustar SXE/SXF diretamente como substituto das rotinas suportadas.

## Perguntas obrigatórias quando houver incerteza
- Qual empresa/filial e ambiente? Existe outro banco parecido?
- O alias/campo foi confirmado no dicionário ativo? Há tabela física identificada?
- É somente leitura, elaboração de código ADVPL/TLPP ou execução que altera dados?
- Existe rotina padrão/API para a operação? Há impactos fiscal, financeiro, estoque, lotes, seriais e EAI?
- Há janela de homologação, backup e plano de reversão? Quem aprova?
