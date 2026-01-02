import subprocess
import os
import csv
import time

HOME = os.path.expanduser("~")
CH_BIN = os.path.join(HOME, "clickhouse/bin/clickhouse")
PG_BIN = os.path.join(HOME, "installs/bin")
TPCH_DIR = os.path.join(HOME, "tpch_kit/dbgen")
PG_DATA = os.path.join(HOME, "installs/data")
TABLES = ["customer", "lineitem", "nation", "orders", "part", "partsupp", "region", "supplier"]

def run(cmd, cwd=None):
    subprocess.run(cmd, shell=True, cwd=cwd, check=True)

def setup_pg_clickhouse():
    status = subprocess.run(
        f"{PG_BIN}/pg_ctl -D {PG_DATA} status",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if(status.returncode!=0):
        print("\nPostgreSQL is not running. Starting server...")
        run(f"{PG_BIN}/pg_ctl -D {PG_DATA} -l logfile start")
    else:
        print("\nPostgreSQL server is already running.")
    
    #run(f'{PG_BIN}/psql -p 5432 -d tpch -c "DROP TABLE IF EXISTS customer, lineitem, nation, orders, part, partsupp, region, supplier CASCADE;"')
    
    run(f'{PG_BIN}/psql -p 5432 -d tpch -c "CREATE EXTENSION IF NOT EXISTS pg_clickhouse;"')

    run(f'{PG_BIN}/psql -p 5432 -d tpch -c "CREATE SCHEMA IF NOT EXISTS clickhouse;"')

    run(f'{PG_BIN}/psql -p 5432 -d tpch -c "DROP SERVER IF EXISTS ch1 CASCADE;"')

    run(f'{PG_BIN}/psql -p 5432 -d tpch -c "CREATE SERVER ch1 FOREIGN DATA WRAPPER clickhouse_fdw OPTIONS(host \'127.0.0.1\', port \'8123\');"')

    run(f'{PG_BIN}/psql -p 5432 -d tpch -c "CREATE USER MAPPING FOR CURRENT_USER SERVER ch1 OPTIONS(user \'default\', password \'\');"')

    run(f'{PG_BIN}/psql -p 5432 -d tpch -f ./pgch.sql')

    run(f'{PG_BIN}/psql -p 5432 -d tpch -c "SET search_path TO clickhouse, public;"')

def run_tpch_queries():
    out = os.path.join(HOME, "pg_clickhouse_tpch_results.csv")
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Query","Trial1_Time(ms)","Trial2_Time(ms)","Trial3_Time(ms)","Average_Time(ms)"])
        queries = [1,3,6,10,12,14]
        for i in queries:
            times = []
            for r in range(3):
                cmd = (f'PGOPTIONS="-c search_path=clickhouse" '#Sets the search path to Clickhouse Schemas
                       f'{PG_BIN}/psql -p 5432 -d tpch -q -t '
                       f'-c "\\timing on" '
                       f'-f {TPCH_DIR}/queries/{i}.sql '
                       f'| grep "Time:"'
                )
                res = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, check=True)
                ms = float(res.stdout.split(' ')[1])
                times.append(ms)
                print(f"Q{i} Run{r+1}: {ms:.2f} ms")

            avg = (times[0] + times[1] + times[2])/3.0 
            print(f"The Average Execution time of the Query {i} is {avg:.2f} ms\n")          
            writer.writerow([f"Query {i}:"] + times + [avg])
    print(f"\nResults saved to: {out}")

if __name__ == "__main__":
    setup_pg_clickhouse()
    #run_tpch_queries()
    #print("\n Stop the ClickHouse server using the command below:\n")
    print("ch-stop")
