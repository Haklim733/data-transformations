# Overview
This repository is a proof of concept and comparison of the multi-engine approach to data transformations between sqlmesh and dbt data transformation framework:

DuckDB: local development testing
Postgres: Store SQLMesh metadata
Motherduck: data warehouse

# state data
sqlmesh offers simple configuration to host state connection information. However, renaming of connections and schemas causes errors.

Optimizing dbt operations on only modified tables requires access to the dbt artifacts to compare state and results with:
Example: `dbt run --select "result:<status>+" state:modified+ --defer --state ./<dbt-artifact-path>`

The approach taken here is to use a combination of python files and macros (i.e. `python dbt/macro/import_artifacts.py`, `python dbt/macros/export_artifacts.sql`) prior and after dbt operations since macros can not install files before dbt operations but on-end-run macro to utilize dbt parameters.

switching between branches triggers pre-commit to run python dbt/macros/import_artifacts.py. Must install the post-checkout hook via `uv run pre-commit install --hook-type post-checkout`


# Troubleshoot

uv add 'sqlmesh[postgres]' results in an error. See https://github.com/TobikoData/sqlmesh/issues/3067
tried: `sudo apt install libpq-dev python3-dev build-essential, postgresql-server-dev-all' on host machine
resolved: `sudo apt install clang`

if running sqlmesh ui and duckdb as the processing engine, sqlmesh cli will not work due to locks on the duckdb database.
