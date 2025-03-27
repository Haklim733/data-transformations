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
    
    logger.info("ingesting dbt artifacts")
    conn.execute("""CREATE OR REPLACE TABLE dbt_artifacts AS
    WITH 
    manifest AS (
        SELECT content 
        FROM read_text('dbt/target/manifest.json')
    ),
    run_results AS (
        SELECT content 
        FROM read_text('dbt/target/run_results.json')
    ),
    semantic AS (
        SELECT content 
        FROM read_text('dbt/target/semantic_manifest.json')
    )
        SELECT
            json_extract_string(m.content, '$.metadata.invocation_id') AS invocation_id,
            json_extract_string(m.content, '$.metadata.generated_at') AS generated_at,
            m.content AS manifest,
            r.content AS run_results,
            s.content AS semantic_manifest
        FROM 
            manifest m
        CROSS JOIN run_results r
        CROSS JOIN semantic s;
    """) 
    logger.info("exporting dbt artifacts to postgres")
    conn.execute("""
    INSERT INTO postgres.public.dbt_artifacts (invocation_id, generated_at, manifest, run_results, semantic_manifest)
    SELECT invocation_id, generated_at, manifest, run_results, semantic_manifest
    FROM dbt_artifacts;
    """)
    conn.close()

if __name__ == "__main__":
    main()