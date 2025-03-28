import logging
import os
import duckdb

logger = logging.getLogger(__name__)

DB_USER = os.getenv("SUPABASE_DB_USER", "postgres")
DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "postgres")
DB_HOST = os.getenv("SUPABASE_DB_HOST", "localhost")
DB_PORT = os.getenv("SUPABASE_DB_PORT", "5432")

def main():
    conn = duckdb.connect()
    conn.execute("INSTALL POSTGRES; LOAD POSTGRES;")
    config = f'dbname=postgres user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}'
    conn.execute(f"ATTACH '{config}' AS postgres (TYPE postgres, SCHEMA 'public');")
    conn.execute("""
        COPY (  
                SELECT manifest::JSON::VARCHAR
                FROM postgres.public.dbt_artifacts
                WHERE target_name = 'prod'
                ORDER BY generated_at DESC
                LIMIT 1
        ) TO './dbt/state/manifest.json' (FORMAT CSV, HEADER FALSE, QUOTE '', DELIMITER '');
    """)

    conn.execute("""
    COPY (
        SELECT run_results::JSON::VARCHAR
        FROM postgres.public.dbt_artifacts
        WHERE target_name = 'prod'
        ORDER BY generated_at DESC
        LIMIT 1
    ) TO './dbt/state/run_results.json' WITH (FORMAT CSV, HEADER FALSE, QUOTE '', DELIMITER '');
    """)
    conn.execute("""
    COPY (
        SELECT semantic_manifest::JSON::VARCHAR
        FROM postgres.public.dbt_artifacts
        WHERE target_name = 'prod'
        ORDER BY generated_at DESC
        LIMIT 1
    ) TO './dbt/state/semantic_manifest.json' WITH (FORMAT CSV, HEADER FALSE, QUOTE '', DELIMITER '');
    """)
    conn.close()

    logger.info("dbt artifacts imported")

if __name__ == "__main__":
    main()