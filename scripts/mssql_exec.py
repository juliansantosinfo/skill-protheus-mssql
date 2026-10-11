#!/usr/bin/env python3
"""
mssql_exec.py - Executor autossuficiente e leve para Microsoft SQL Server / TOTVS Protheus.
Zero dependências externas: utiliza exclusivamente a biblioteca padrão do Python 3.
Suporta execução direta via Docker (ex.: totvs_mssql), sqlcmd no host ou drivers Python instalados.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


def parse_env_file(file_path):
    """Lê arquivo .env sem bibliotecas externas."""
    values = {}
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        return values
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                        v = v[1:-1]
                    values[k] = v
    except Exception as e:
        sys.stderr.write(f"Aviso: erro ao ler {path}: {e}\n")
    return values


def resolve_config(env_file_arg=None):
    """Resolve configurações usando exclusivamente o arquivo .env na raiz do projeto (cwd)."""
    if env_file_arg:
        target_env = Path(env_file_arg).expanduser().resolve()
    else:
        target_env = Path.cwd() / ".env"

    if not target_env.is_file():
        raise ValueError(
            f"Arquivo .env não encontrado na raiz do projeto ({target_env}). "
            "Solicite ao usuário os dados de conexão (MSSQL_HOST, MSSQL_DATABASE, MSSQL_USER, MSSQL_PASSWORD) "
            "e crie o arquivo .env antes de executar."
        )

    env_data = parse_env_file(target_env)

    def get_val(key, default=""):
        return os.environ.get(key, env_data.get(key, default))

    # Validação obrigatória de credenciais
    required_keys = ["MSSQL_HOST", "MSSQL_DATABASE", "MSSQL_USER", "MSSQL_PASSWORD"]
    missing = [k for k in required_keys if not get_val(k)]
    if missing:
        raise ValueError(
            f"Arquivo .env ({target_env}) incompleto. Variáveis ausentes: {', '.join(missing)}. "
            "Solicite esses valores ao usuário e atualize o .env antes de continuar."
        )

    host = get_val("MSSQL_HOST")
    port = int(get_val("MSSQL_PORT", "1433"))
    database = get_val("MSSQL_DATABASE")
    user = get_val("MSSQL_USER")
    password = get_val("MSSQL_PASSWORD")
    client = get_val("MSSQL_CLIENT", "auto").lower()
    container = get_val("MSSQL_DOCKER_CONTAINER", "")
    timeout = int(get_val("MSSQL_COMMAND_TIMEOUT", "30"))
    trust_cert = get_val("MSSQL_TRUST_SERVER_CERTIFICATE", "yes").lower() in ("yes", "true", "1")
    encrypt = get_val("MSSQL_ENCRYPT", "yes").lower() in ("yes", "true", "1")
    sqlcmd_path = get_val("MSSQL_SQLCMD_PATH", "")

    return {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
        "client": client,
        "container": container,
        "timeout": timeout,
        "trust_cert": trust_cert,
        "encrypt": encrypt,
        "sqlcmd_path": sqlcmd_path,
        "env_path": str(target_env),
    }



def find_docker_container(preferred=""):
    """Localiza container docker do SQL Server se o Docker estiver ativo."""
    if not shutil.which("docker"):
        return None
    try:
        if preferred:
            res = subprocess.run(
                ["docker", "ps", "--filter", f"name={preferred}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            containers = [c.strip() for c in res.stdout.strip().splitlines() if c.strip()]
            if preferred in containers:
                return preferred
            if containers:
                return containers[0]

        # Busca automática por containers com mssql no nome
        res = subprocess.run(
            ["docker", "ps", "--filter", "name=mssql", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        containers = [c.strip() for c in res.stdout.strip().splitlines() if c.strip()]
        if containers:
            return containers[0]
    except Exception:
        pass
    return None


def find_container_sqlcmd(container):
    """Encontra o binário do sqlcmd dentro do container Docker."""
    candidates = [
        "/opt/mssql-tools18/bin/sqlcmd",
        "/opt/mssql-tools/bin/sqlcmd",
        "sqlcmd",
    ]
    for cand in candidates:
        try:
            res = subprocess.run(
                ["docker", "exec", container, "which", cand],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
    return "/opt/mssql-tools18/bin/sqlcmd"


def determine_backend(cfg):
    """Determina o backend de execução: docker, sqlcmd ou python."""
    client_choice = cfg["client"]

    if client_choice == "docker":
        container = find_docker_container(cfg["container"])
        if not container:
            raise RuntimeError(f"Container Docker não encontrado para MSSQL (configurado: {cfg['container']})")
        return "docker", container

    if client_choice == "sqlcmd":
        exe = cfg["sqlcmd_path"] or shutil.which("sqlcmd")
        if not exe:
            raise RuntimeError("Binário sqlcmd não encontrado no host")
        return "sqlcmd", exe

    if client_choice == "python":
        return "python", None

    # Modo AUTO:
    # 1. Se estiver conectando a localhost/127.0.0.1 e houver container Docker mssql ativo, usa Docker (zero-install)
    is_local = cfg["host"] in ("127.0.0.1", "localhost", "0.0.0.0")
    if is_local:
        container = find_docker_container(cfg["container"] or "totvs_mssql")
        if container:
            return "docker", container

    # 2. Se houver sqlcmd no host
    exe = cfg["sqlcmd_path"] or shutil.which("sqlcmd")
    if exe:
        return "sqlcmd", exe

    # 3. Se houver container docker ativo (mesmo para host remoto, pode fazer ponte)
    container = find_docker_container(cfg["container"])
    if container:
        return "docker", container

    # 4. Fallback para python se instalado
    return "python", None


def parse_sqlcmd_tabular(output_text):
    """Converte saída tabular tab-separated do sqlcmd em lista de dicionários."""
    lines = [line.rstrip("\r\n") for line in output_text.splitlines() if line.strip()]
    if not lines:
        return []

    # Ignora linhas informativas do SQL Server (ex: Changed database context, rows affected)
    filtered = []
    for l in lines:
        if l.startswith("(") and ("rows affected" in l or "row affected" in l):
            continue
        if l.startswith("Changed database context to"):
            continue
        filtered.append(l)

    if len(filtered) < 2:
        return []

    # Primeira linha: Cabeçalhos
    headers = [h.strip() for h in filtered[0].split("\t")]
    # Segunda linha: Separador de traços (ex: ------  -------)
    data_lines = filtered[2:] if len(filtered) >= 2 and all(c in "- \t" for c in filtered[1]) else filtered[1:]

    rows = []
    for line in data_lines:
        parts = [p.strip() for p in line.split("\t")]
        # Preenche com vazio se partes < headers
        while len(parts) < len(headers):
            parts.append("")
        row_dict = {}
        for h, v in zip(headers, parts):
            row_dict[h] = None if v == "NULL" else v
        rows.append(row_dict)

    return rows


def run_sqlcmd_command(backend_type, target, cfg, sql_content):
    """Executa SQL via sqlcmd (seja no container Docker ou no host)."""
    # Monta parâmetros do sqlcmd
    # -S host,porta
    # -U user
    # -d database
    # -W (remove trailing spaces)
    # -s "\t" (delimitador tab)
    # -b (on error return non-zero exit code)
    # -C (trust server certificate)
    # -N (encrypt)
    is_docker = backend_type == "docker"
    sqlcmd_bin = find_container_sqlcmd(target) if is_docker else target

    # Se for docker e host for local, conecta em localhost dentro do container
    server_conn = "localhost" if (is_docker and cfg["host"] in ("127.0.0.1", "localhost")) else f"tcp:{cfg['host']},{cfg['port']}"

    cmd = []
    if is_docker:
        cmd.extend(["docker", "exec", "-i", "-e", f"SQLCMDPASSWORD={cfg['password']}", target, sqlcmd_bin])
    else:
        cmd.append(sqlcmd_bin)

    cmd.extend([
        "-S", server_conn,
        "-U", cfg["user"],
        "-d", cfg["database"],
        "-W",
        "-s", "\t",
        "-b",
        "-t", str(cfg["timeout"]),
    ])

    # No Docker com certificado autoassinado ou quando configurado, confia no certificado (-C)
    if cfg["trust_cert"] or is_docker:
        cmd.append("-C")
    if cfg["encrypt"] and not (cfg["trust_cert"] or is_docker):
        cmd.append("-N")

    env = os.environ.copy()
    if not is_docker:
        env["SQLCMDPASSWORD"] = cfg["password"]

    # Garante que SQL execute sem contar linhas desnecessárias
    prepared_sql = f"SET NOCOUNT ON;\n{sql_content.strip()}\n"

    res = subprocess.run(
        cmd,
        input=prepared_sql,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=cfg["timeout"] + 10,
    )

    if res.returncode != 0:
        err_msg = res.stdout.strip() or res.stderr.strip() or f"Erro sqlcmd com código de saída {res.returncode}"
        # Remove eventuais senhas da mensagem de erro
        if cfg["password"]:
            err_msg = err_msg.replace(cfg["password"], "********")
        raise RuntimeError(err_msg)

    return res.stdout


def run_python_driver(cfg, sql_content):
    """Fallback usando pymssql ou pyodbc se instalados."""
    try:
        import pymssql
        conn = pymssql.connect(
            server=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            timeout=cfg["timeout"],
            as_dict=True,
        )
        cur = conn.cursor()
        cur.execute(sql_content)
        try:
            rows = cur.fetchall()
        except Exception:
            rows = []
        conn.commit()
        conn.close()
        return rows
    except ImportError:
        pass

    try:
        import pyodbc
        driver = os.environ.get("MSSQL_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
        trust = "yes" if cfg["trust_cert"] else "no"
        conn_str = f"DRIVER={{{driver}}};SERVER=tcp:{cfg['host']},{cfg['port']};DATABASE={cfg['database']};UID={cfg['user']};PWD={cfg['password']};TrustServerCertificate={trust};Connection Timeout={cfg['timeout']}"
        conn = pyodbc.connect(conn_str, autocommit=True)
        cur = conn.cursor()
        cur.execute(sql_content)
        if cur.description:
            cols = [c[0] for c in cur.description]
            data = cur.fetchall()
            rows = [dict(zip(cols, [None if v is None else str(v) for v in r])) for r in data]
        else:
            rows = []
        conn.close()
        return rows
    except ImportError:
        raise RuntimeError(
            "Nenhum cliente disponível: sqlcmd não encontrado no host nem via container Docker, "
            "e nenhum módulo Python (pymssql ou pyodbc) está instalado."
        )


def check_protheus_warning(sql):
    """Alerta sobre riscos ao tentar gravar diretamente em tabelas Protheus."""
    write_pattern = r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE)\b"
    if re.search(write_pattern, sql, re.IGNORECASE):
        # Tabelas de negócio clássicas e dicionários
        protheus_targets = r"\b(S[A-Z0-9]{2}[0-9]{3,}|SX[1-9][0-9]{3,}|SIX[0-9]{3,})\b"
        matches = re.findall(protheus_targets, sql, re.IGNORECASE)
        if matches:
            return (
                f"ATENÇÃO PROTHEUS: O comando afeta diretamente tabelas Protheus ({', '.join(set(matches))}). "
                "Gravação direta via SQL ignora validações de dicionário (SX3), regras MVC, triggers (SX7), "
                "pontos de entrada e controle de numeração (SXE/SXF). "
                "Recomenda-se implementar via ADVPL/TLPP (MsExecAuto, MVC ou RecLock)."
            )
    return None


def cmd_ping(args, cfg):
    """Verifica conectividade e obtém metadados do banco."""
    backend_type, target = determine_backend(cfg)

    sql = """
    SELECT 
        DB_NAME() AS database_name,
        @@SERVERNAME AS server_name,
        SYSTEM_USER AS connected_login,
        CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(100)) AS product_version,
        (SELECT COUNT(*) FROM sys.tables WHERE name LIKE 'SX%') AS sx_tables_count,
        (SELECT COUNT(*) FROM sys.tables WHERE name LIKE 'SA1%') AS sa1_tables_count;
    """

    if backend_type in ("docker", "sqlcmd"):
        raw = run_sqlcmd_command(backend_type, target, cfg, sql)
        rows = parse_sqlcmd_tabular(raw)
        info = rows[0] if rows else {}
    else:
        rows = run_python_driver(cfg, sql)
        info = rows[0] if rows else {}

    is_protheus = int(info.get("sx_tables_count", 0) or 0) > 0 or int(info.get("sa1_tables_count", 0) or 0) > 0

    result = {
        "ok": True,
        "backend": backend_type,
        "target": str(target),
        "database": info.get("database_name", cfg["database"]),
        "server": info.get("server_name", cfg["host"]),
        "user": info.get("connected_login", cfg["user"]),
        "version": info.get("product_version", ""),
        "is_protheus": is_protheus,
        "config_env": cfg["env_path"],
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Status: CONECTADO COM SUCESSO")
        print(f"Backend: {result['backend']} ({result['target']})")
        print(f"Banco: {result['database']} | Servidor: {result['server']} | Usuário: {result['user']}")
        print(f"Versão MSSQL: {result['version']}")
        print(f"Ambiente Protheus Detectado: {'SIM' if is_protheus else 'NÃO'}")
        if cfg["env_path"]:
            print(f"Configuração carregada de: {cfg['env_path']}")


def cmd_query(args, cfg):
    """Executa consultas de leitura (SELECT)."""
    sql = args.sql if args.sql else Path(args.file).read_text(encoding="utf-8-sig")
    backend_type, target = determine_backend(cfg)

    # Injeta limite TOP se solicitado e não presente
    clean_sql = sql.strip().rstrip(";")

    if backend_type in ("docker", "sqlcmd"):
        raw = run_sqlcmd_command(backend_type, target, cfg, clean_sql)
        rows = parse_sqlcmd_tabular(raw)
    else:
        rows = run_python_driver(cfg, clean_sql)

    # Aplica limite no resultado se especificado
    if args.limit and len(rows) > args.limit:
        rows = rows[: args.limit]
        truncated = True
    else:
        truncated = False

    if args.format == "json":
        out = {
            "ok": True,
            "backend": backend_type,
            "count": len(rows),
            "truncated": truncated,
            "rows": rows,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.format == "raw":
        if backend_type in ("docker", "sqlcmd"):
            print(raw)
        else:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        # Formato tabela simples
        if not rows:
            print("Nenhum registro retornado.")
            return
        headers = list(rows[0].keys())
        col_widths = {h: len(h) for h in headers}
        for r in rows:
            for h in headers:
                val_str = str(r.get(h, ""))
                col_widths[h] = max(col_widths[h], min(len(val_str), 50))

        header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
        sep_line = "-+-".join("-" * col_widths[h] for h in headers)
        print(header_line)
        print(sep_line)
        for r in rows:
            line = " | ".join(str(r.get(h, "") if r.get(h) is not None else "NULL")[:50].ljust(col_widths[h]) for h in headers)
            print(line)
        print(f"\n({len(rows)} registro(s){' - limitado' if truncated else ''})")


def cmd_execute(args, cfg):
    """Executa comandos DML/DDL com proteção transacional por padrão."""
    sql = args.sql if args.sql else Path(args.file).read_text(encoding="utf-8-sig")
    backend_type, target = determine_backend(cfg)

    warning = check_protheus_warning(sql)
    if warning:
        sys.stderr.write(f"\n[AVISO] {warning}\n\n")

    apply_changes = getattr(args, "apply", False)
    ack_confirm = getattr(args, "ack", "") == "confirmed"

    if apply_changes and not ack_confirm:
        raise ValueError("Para persistir alterações é obrigatório informar: --apply --ack confirmed")

    # Envolve em bloco transacional com ROLLBACK se for modo PREVIEW
    if not apply_changes:
        wrapped_sql = f"""
        SET XACT_ABORT ON;
        BEGIN TRANSACTION;
        {sql.strip()};
        SELECT @@ROWCOUNT AS affected_rows;
        ROLLBACK TRANSACTION;
        """
        mode_desc = "PREVIEW (Simulação com ROLLBACK)"
    else:
        wrapped_sql = f"""
        SET XACT_ABORT ON;
        BEGIN TRANSACTION;
        {sql.strip()};
        SELECT @@ROWCOUNT AS affected_rows;
        COMMIT TRANSACTION;
        """
        mode_desc = "PERSISTED (Alterações aplicadas com COMMIT)"

    if backend_type in ("docker", "sqlcmd"):
        raw = run_sqlcmd_command(backend_type, target, cfg, wrapped_sql)
        rows = parse_sqlcmd_tabular(raw)
        affected = rows[0].get("affected_rows", "?") if rows else "?"
    else:
        rows = run_python_driver(cfg, wrapped_sql)
        affected = rows[0].get("affected_rows", "?") if rows else "?"

    result = {
        "ok": True,
        "backend": backend_type,
        "mode": mode_desc,
        "persisted": apply_changes,
        "affected_rows": affected,
        "warning": warning,
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Modo: {mode_desc}")
        print(f"Backend: {backend_type} ({target})")
        print(f"Linhas afetadas: {affected}")
        if not apply_changes:
            print("\n>> Nenhuma alteração foi gravada. Para gravar efetivamente, adicione: --apply --ack confirmed")


def main():
    sub_base_parser = argparse.ArgumentParser(add_help=False)
    sub_base_parser.add_argument("--env-file", default=argparse.SUPPRESS, help="Caminho explícito para arquivo de conexão .env")
    sub_base_parser.add_argument("--client", choices=["auto", "docker", "sqlcmd", "python"], default=argparse.SUPPRESS, help="Forçar backend de execução")
    sub_base_parser.add_argument("--container", default=argparse.SUPPRESS, help="Nome do container Docker do SQL Server (padrão: totvs_mssql ou autodetect)")
    sub_base_parser.add_argument("--format", choices=["json", "table", "raw"], default=argparse.SUPPRESS, help="Formato de saída (padrão: json)")

    parser = argparse.ArgumentParser(
        description="Executor MSSQL zero-dependências para TOTVS Protheus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--env-file", default=None, help="Caminho explícito para arquivo de conexão .env")
    parser.add_argument("--client", choices=["auto", "docker", "sqlcmd", "python"], default=None, help="Forçar backend de execução")
    parser.add_argument("--container", default=None, help="Nome do container Docker do SQL Server (padrão: totvs_mssql ou autodetect)")
    parser.add_argument("--format", choices=["json", "table", "raw"], default="json", help="Formato de saída (padrão: json)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando: ping
    subparsers.add_parser("ping", parents=[sub_base_parser], help="Testa conectividade e valida metadados do banco")

    # Subcomando: query
    p_query = subparsers.add_parser("query", parents=[sub_base_parser], help="Executa consulta SELECT de leitura")
    g_query = p_query.add_mutually_exclusive_group(required=True)
    g_query.add_argument("--sql", help="Comando SQL direto")
    g_query.add_argument("--file", help="Caminho para arquivo .sql")
    p_query.add_argument("--limit", type=int, default=10, help="Limite máximo de linhas (padrão: 10)")

    # Subcomando: execute
    p_exec = subparsers.add_parser("execute", parents=[sub_base_parser], help="Executa comando SQL (DML/DDL) com proteção transacional")
    g_exec = p_exec.add_mutually_exclusive_group(required=True)
    g_exec.add_argument("--sql", help="Comando SQL direto")
    g_exec.add_argument("--file", help="Caminho para arquivo .sql")
    p_exec.add_argument("--apply", action="store_true", help="Aplica e persiste as alterações (COMMIT)")
    p_exec.add_argument("--ack", choices=["confirmed"], help="Confirmação explícita para aplicação ('confirmed')")

    args = parser.parse_args()

    try:
        cfg = resolve_config(args.env_file)
        if args.client:
            cfg["client"] = args.client
        if args.container:
            cfg["container"] = args.container

        if args.command == "ping":
            cmd_ping(args, cfg)
        elif args.command == "query":
            cmd_query(args, cfg)
        elif args.command == "execute":
            cmd_execute(args, cfg)
    except Exception as e:
        err_payload = {"ok": False, "error": str(e)}
        if args.format == "json":
            print(json.dumps(err_payload, ensure_ascii=False, indent=2))
        else:
            sys.stderr.write(f"\nERRO: {e}\n\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
