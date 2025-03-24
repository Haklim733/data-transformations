# Overview
This repository reflects a multi-engine, isolated systems approach to data transformations using sqlmesh.

It utilizes motherduck, postgres (supabase) as sources and duckdb as the local processing engine for dev and motherduck as the datawarehouse.

# isolated systems
This repository follows a isolated systems design with separate databases for production and dev (local). As such, separate 'state' databases via supabase are employed as detailed in the [documentation](https://sqlmesh.readthedocs.io/en/stable/guides/isolated_systems/?h=isolated#terminology).

# Troubleshoot

uv add 'sqlmesh[postgres]' results in an error. See https://github.com/TobikoData/sqlmesh/issues/3067
tried: `sudo apt install libpq-dev python3-dev build-essential, postgresql-server-dev-all' on host machine
resolved: `sudo apt install clang`
