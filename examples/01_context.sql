SELECT DB_NAME() AS database_name,
       @@SERVERNAME AS server_name,
       SYSTEM_USER AS connected_login,
       CURRENT_USER AS database_user,
       CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(100)) AS product_version;
