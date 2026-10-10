# Descoberta do dicionário Protheus

## O que consultar
- SX1: perguntas de rotinas; SX2: cadastro de tabelas, alias, mapeamento físico e modos de compartilhamento; SX3: campos, títulos, tipos, tamanhos e validações; SIX: ordens/índices lógicos; SX5: tabelas genéricas; SX6: parâmetros MV_*; SX7: gatilhos de campos; SX9: relacionamentos; SXA: pastas; SXB: consultas padrão; SXG: grupos de campos; SXE/SXF: controle de numeração (extremamente sensível).
- Não confundir índice lógico SIX com índice SQL Server em `sys.indexes`; ambos podem diferir. Nem todos os relacionamentos SX9 são constraints SQL físicas.
- O repositório efetivo do dicionário pode ser arquivo/metadado gerenciado pelo Protheus e **não** estar exposto em tabelas SQL Server. Nunca presumir `SELECT * FROM SX3010` ou que um prefixo SX representa necessariamente o dicionário ativo.

## Procedimento
1. Consultar `sys.tables`, `sys.schemas`, `sys.columns` para localizar objetos candidatos SX e de negócio (sem varrer dados inteiros).
2. Se uma SX física for encontrada, confirmar que corresponde ao dicionário ativo da instância e versão: verificar campos (`X2_CHAVE`, `X2_ARQUIVO`, `X2_MODOEMP`, `X2_MODO`, `X3_ARQUIVO`, `X3_CAMPO`, conforme existam), tamanho, codificação e compartilhamento. Campos variam entre releases/customizações.
3. Para catálogo `SX2`: conferir alias lógico, nome físico e modos de compartilhamento. Para `SX3`: identificar campos reais e critérios obrigatórios, mas nunca presumir que validações do framework equivalem a constraints SQL.
4. Na ausência de SX no SQL: solicitar saída do Configurador (SIGACFG) ou método de leitura do dicionário ativo no AppServer, ou autorização para gerar uma rotina diagnóstica ADVPL/TLPP **somente leitura**. Os metadados obtidos por esses meios têm precedência sobre sites ou exemplos.
5. Ao analisar `SX6`, considerar contexto da empresa/filial e cache/ambiente; não inferir parâmetro de produção a partir de configuração de homologação.
6. **Nunca atualizar/inserir/excluir SX ou objetos de dicionário via SQL bruto**; utilizar Configurador/atualizações suportadas e processo formal.

## Fontes de validação
- TOTVS TDN: https://tdn.totvs.com/display/framework/SX2+-+Tabelas+de+Dados
- TOTVS TDN: https://tdn.totvs.com/pages/releaseview.action?pageId=22479539
- Documentação oficial específica da release e ambiente do cliente prevalece sobre catálogos externos.
