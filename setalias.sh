#!/usr/bin/env bash

BASHRC="$HOME/.bashrc"

add_alias() {
    local name="$1"
    local value="$2"

    # Check if alias already exists
    if grep -q "^alias $name=" "$BASHRC"; then
        echo "Alias already exists: $name"
    else
        echo "alias $name=\"$value\"" >> "$BASHRC"
        echo "Added alias: $name"
    fi
}

add_alias ch-start "$HOME/clickhouse/bin/clickhouse server --config-file=$HOME/clickhouse/etc/clickhouse-server/config.xml"
add_alias ch-stop "pkill -f 'clickhouse server'"
source "$BASHRC"
