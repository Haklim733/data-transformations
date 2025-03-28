{% macro export_artifacts() %}
    {% set dbt_target_path = target.path %}
    {% set dbt_target_name = target.name%}
    
    {{ log("Exporting dbt artifacts to Postgres via duckdb", info=True) }}
    {{ log(target, info=True) }}
    
    {% set postgres_config %}
        dbname=postgres 
        user={{ env_var('SUPABASE_DB_USER', 'postgres') }} 
        password={{ env_var('SUPABASE_DB_PASSWORD', 'postgres') }} 
        host={{ env_var('SUPABASE_DB_HOST', 'localhost') }} 
        port={{ env_var('SUPABASE_DB_PORT', '5432') }}
    {% endset %}
    
    {% set sql %}

    {% if target.type != 'duckdb' %}
        {% set target %}
            database=target.database
            schema=target.schema
            path=local.db
            type='duckdb'
        {% endset %}

        INSTALL POSTGRES;
        LOAD POSTGRES;
        ATTACH '{{ postgres_config }}' AS postgres (TYPE postgres, SCHEMA 'public');
    {% endif %}
    
     
        CREATE OR REPLACE TABLE dbt_artifacts AS
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
            s.content AS semantic_manifest,
            json_extract_string(m.content, '$.metadata.user_id') AS user_id,
            json_extract_string(m.content, '$.metadata.project_name') AS project_name,
            '{{ target.database}}' AS db_name,
            '{{ target.schema}}' AS schema_name,
            '{{ target.name }}' AS target_name 
        FROM 
            manifest m
        CROSS JOIN run_results r
        CROSS JOIN semantic s;
        
        INSERT INTO postgres.public.dbt_artifacts (invocation_id, generated_at, manifest, run_results, semantic_manifest, user_id, project_name, db_name, schema_name, target_name)
        SELECT invocation_id, generated_at, manifest, run_results, semantic_manifest, user_id, project_name, db_name, schema_name, target_name
        FROM dbt_artifacts;
        

        {% endset %}
        
         
    {% if target.name != 'local' %}
        {% do run_query(sql) %}
        {{ log("dbt artifacts successfully exported to Postgres", info=True) }}
    {% else %}
        {{ log("dbt artifacts not exported. Target is " ~ target.name, info=True) }} 
    {% endif %}
    
{% endmacro %}