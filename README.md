# Troubleshoot

uv add 'sqlmesh[postgres]' results in an error. See https://github.com/TobikoData/sqlmesh/issues/3067
tried: `sudo apt install libpq-dev python3-dev build-essential, postgresql-server-dev-all' on host machine
resolved: `sudo apt install clang`
