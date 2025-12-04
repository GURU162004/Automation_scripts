import subprocess
import time

PG_BIN = "/home/your_user/pgsql_git/bin/psql"  # Adjust path to your psql binary
DB_NAME = "tpch"
PORT = "5433"
QUERY_FILES = [
    "/home/your_user/tpch-kit/queries/q1.sql",
    "/home/your_user/tpch-kit/queries/q2.sql",
    # Add more query files here
]

for qfile in QUERY_FILES:
    print(f"Running {qfile} ...")
    start = time.time()
    result = subprocess.run(
        [PG_BIN, "-p", PORT, "-d", DB_NAME, "-f", qfile],
        capture_output=True,
        text=True
    )
    end = time.time()
    elapsed = end - start

    if result.returncode != 0:
        print(f"Error running {qfile}: {result.stderr}")
    else:
        print(f"Query {qfile} executed in {elapsed:.3f} seconds\n")
        # Optional: print query output with: print(result.stdout)
