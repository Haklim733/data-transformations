{% macro import_artifacts() %}
    {% set state_dir = 'dbt/state' %}
    
    {{ log("Importing dbt artifacts from Postgres to " ~ state_dir, info=True) }}
    
    
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
        ATTACH '{{ postgres_config }}' AS postgres (TYPE postgres, SCHEMA 'public', READ_ONLY TRUE);
    
    {% endif %}

    COPY (
        SELECT manifest::JSON::VARCHAR
        FROM postgres.public.dbt_artifacts
        WHERE target_name = 'prod'
        ORDER BY generated_at DESC
        LIMIT 1
    ) TO 'dbt/state/manifest.json' (FORMAT CSV, HEADER FALSE, QUOTE '', DELIMITER '', OVERWRITE TRUE);
    
    COPY (
        SELECT run_results::JSON::VARCHAR
        FROM postgres.public.dbt_artifacts
        WHERE target_name = 'prod'
        ORDER BY generated_at DESC
        LIMIT 1
    ) TO 'dbt/state/run_results.json' (FORMAT CSV, HEADER FALSE, QUOTE '', DELIMITER '', OVERWRITE TRUE);
    
    COPY (
        SELECT semantic_manifest::JSON::VARCHAR
        FROM postgres.public.dbt_artifacts
        WHERE target_name = 'prod'
        ORDER BY generated_at DESC
        LIMIT 1
    ) TO 'dbt/state/semantic_manifest.json' (FORMAT CSV, HEADER FALSE, QUOTE '', DELIMITER '', OVERWRITE TRUE);
    {% endset %}
    
    {% do run_query(sql) %}
    
    {{ log("dbt artifacts successfully imported to " ~ state_dir, info=True) }}
    
{% endmacro %}