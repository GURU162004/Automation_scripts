import subprocess
import os

HOME = os.path.expanduser("~")
CH_BIN = os.path.join(HOME, "clickhouse/bin/clickhouse")
TPCH_DIR = os.path.join(HOME, "tpch_kit/dbgen")

TABLES = ["customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"]

def run(cmd, cwd=None):
    subprocess.run(cmd, shell=True, cwd=cwd, check=True)

def setup_clickhouse():
    run(f'{CH_BIN} client -q "CREATE DATABASE IF NOT EXISTS tpch;"')
    run(f'{CH_BIN} client --multiquery < ./ch.sql')
    run(f'{CH_BIN} client -q "SHOW TABLES FROM tpch"')

    for t in TABLES:
        run(f'{CH_BIN} client -q "INSERT INTO tpch.{t} FORMAT CSV" --format_csv_delimiter="|" < {TPCH_DIR}/{t}.tbl')

def check_clickhouse():
    try:
        run(f'{CH_BIN} client -q "SELECT 1"')
    except:
        print("ClickHouse server is not running. Start it using ch-start.")
        exit(1)

if __name__ == "__main__":
    print("Start the Clickhouse server, if not started using the command below:\n")
    print("ch-start\n")
    yes = input("If started enter Y: ")
    if yes=='y' or yes=='Y':
        check_clickhouse()
        setup_clickhouse()
        print("Proceed and run the pg_clickhouse_tpch script")