-- T-103: esquemas e papéis. Sem senha aqui: o executor (loader/migrar.py) aplica a senha do app_ro a partir do ambiente.
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS resultado;
CREATE SCHEMA IF NOT EXISTS ops;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'loader_rw') THEN
        CREATE ROLE loader_rw LOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_ro') THEN
        CREATE ROLE app_ro LOGIN;
    END IF;
END
$$;

-- app_ro: nada em stg; leitura em mart e resultado (inclusive tabelas futuras criadas pelo dono).
REVOKE ALL ON SCHEMA stg FROM PUBLIC;
REVOKE ALL ON SCHEMA ops FROM PUBLIC;
GRANT USAGE ON SCHEMA mart, resultado TO app_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA mart, resultado TO app_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT SELECT ON TABLES TO app_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA resultado GRANT SELECT ON TABLES TO app_ro;
