# Overview
This repository is a proof of concept and testing of the multi-engine approach to data transformations using sqlmesh, duckdb, motherduck, and postgres for testing and proof of concept.

# Troubleshoot

uv add 'sqlmesh[postgres]' results in an error. See https://github.com/TobikoData/sqlmesh/issues/3067
tried: `sudo apt install libpq-dev python3-dev build-essential, postgresql-server-dev-all' on host machine
resolved: `sudo apt install clang`

if running sqlmesh ui and duckdb as the processing engine, sqlmesh cli will not work due to locks on the duckdb database.
