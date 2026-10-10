# Especializações futuras

- Uma skill por domínio (`protheus-vendas`, `protheus-comex`, `protheus-estoque`, `protheus-fiscal`) pode incluir exemplos e mapeamentos reais, mas não credenciais e nem valores de filial fixos.
- Resolver conexão pela skill `mssql-database`, Protheus por `protheus-mssql`, regras e rotinas por skill de domínio.
- Requisitos por rotina: alias e tabelas comprovadas, chave lógica, cardinalidade, status e enumerações de campo, testes sobre `D_E_L_E_T_`, regras filial/empresa, origem do dicionário, integração com APIs/PEs e plano de homologação.
- Regras de segurança herdadas são cumulativas: nenhuma skill filha deve autorizar SQL bruto em tabelas de negócio ou dicionário Protheus.
