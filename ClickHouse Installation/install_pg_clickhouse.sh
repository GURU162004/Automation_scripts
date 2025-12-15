#!/usr/bin/env bash

git clone https://github.com/ClickHouse/pg_clickhouse.git
cd pg_clickhouse

export PG_CONFIG=~/pgsql_git/bin/pg_config

make
make install