import subprocess
import sys
import os
import time

DIR_NAME = "pgsql_git"
SOURCE_URL = "https://github.com/postgres/postgres.git"
TPCH_URL = "https://github.com/gregrahn/tpch-kit.git"

HOME_DIR = os.path.expanduser("~")
INSTALL_PATH = os.path.join(HOME_DIR, DIR_NAME)
SOURCE_FOLDER = os.path.join(INSTALL_PATH, "postgres")
TPCH_DIR = os.path.join(HOME_DIR, "tpch_kit")
DATA_DIR = os.path.join(INSTALL_PATH,"data")
BIN_DIR = os.path.join(INSTALL_PATH,"bin")

tables = ["customer","lineitem","nation","orders","part","partsupp","region","supplier"]

def run(command, cwd=None, shell=True, quiet=False):
    print(f"\n Running: {command}")
    try:
        if quiet:
            subprocess.run(command, cwd=cwd, shell=shell, check = True, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        else:
            subprocess.run(command, cwd=cwd, shell=shell, check = True)
    except subprocess.CalledProcessError as e:
        print(f"\nError executing command: {command}")
        print(f"Reason: {e}")
        sys.exit(1)
    
def clone_source():
    if not os.path.exists(INSTALL_PATH):
        os.makedirs(INSTALL_PATH)
    if not os.path.exists(SOURCE_FOLDER):
        print("\n git cloning repository ....")
        run(f"git clone {SOURCE_URL} postgres",cwd=INSTALL_PATH)
    
    print("\n listing branches : ")
    run("git branch -r | grep REL",cwd=SOURCE_FOLDER)
    VERSION = input("Enter Version : ")
    run(f"git checkout REL_{VERSION}_STABLE",cwd=SOURCE_FOLDER)
          
def build_postgres():
    postgres_bin = os.path.join(BIN_DIR,"postgres")
    if os.path.exists(postgres_bin):
        print("\nPostgreSQL is already compiled and installed")
        return
    print("\n Configuring and Compiling ")
    run(f"./configure --prefix={INSTALL_PATH} --with-pgport=5433",cwd=SOURCE_FOLDER)
    run("make",cwd=SOURCE_FOLDER)
    run("make install",cwd=SOURCE_FOLDER)
    
def setup_database():
    print("\n Setting up Database")
    data_dir = os.path.join(INSTALL_PATH,"data")
    if not os.path.exists(data_dir):
        run(f"{BIN_DIR}/initdb -D {data_dir}")
    status = subprocess.run(
        f"{BIN_DIR}/pg_ctl -D {data_dir} status",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if(status.returncode!=0):
        print("\nPostgreSQL is not running. Starting server...")
        run(f"{BIN_DIR}/pg_ctl -D {data_dir} -l logfile start")
    else:
        print("\nPostgreSQL server is already running.")
    
def setup_tpch():
    if not os.path.exists(TPCH_DIR):
        print("\n git cloning repository ....")
        run(f"git clone {TPCH_URL} {TPCH_DIR}")
    else:
        print("\n tpch directory exists")
    dbgen_dir = os.path.join(TPCH_DIR,"dbgen")
    run("make clean",cwd=dbgen_dir,quiet=True)
    run("make MACHINE=LINUX DATABASE=POSTGRESQL",cwd=dbgen_dir,quiet=True)

    if not os.path.exists(os.path.join(TPCH_DIR,"dbgen","supplier.tbl")):
        print("\nGenerating TPC-H data (scale factor 1) ...")
        run("./dbgen -s 1",cwd=dbgen_dir)
    else:
        print("\nTPC-H data already exists, skipping dbgen")

    run(f"{BIN_DIR}/dropdb -p 5433 --if-exists tpch",cwd=dbgen_dir)
    run(f"{BIN_DIR}/createdb -p 5433 tpch",cwd=dbgen_dir)
    run(f"{BIN_DIR}/psql -p 5433 -d tpch -f dss.ddl",cwd=dbgen_dir)
    
    for tbl in tables:
        file = f"{tbl}.tbl"
        sql = f"\\copy {tbl} FROM '{file}' WITH (FORMAT csv, DELIMITER '|', NULL '')"
        run(f'{BIN_DIR}/psql -p 5433 -d tpch -c "{sql}"',cwd=dbgen_dir)
    
    if not os.path.exists(os.path.join(dbgen_dir,"sqlqueries")):
        os.makedirs(os.path.join(dbgen_dir,"sqlqueries"))

    for i in range(1,23):
        run(f"./qgen {i} > /sqlqueries/{i}.sql",cwd=dbgen_dir,quiet=True)

def run_queries():
    for i in range(1,23):
        qfile = "q"+str(i)+".sql"
        run_times = []
        for r in range(3):
            print(f"running {qfile} ...")
            start = time.time()
            run(f'{BIN_DIR}/psql -p 5433 -q -t -A -d tpch -c "\\timing on" -f {TPCH_DIR}/dbgen/sqlqueries/{qfile}')
            run_time = time.time()-start
            print(f"Trial {r+1}: Query {qfile} executed in {run_time:3f} seconds")
            run_times.append(run_time)
        avg = (run_times[0] + run_times[1] + run_times[2])/3.0
        print(f"The Average Execution time of the Query {qfile} is {avg:3f} seconds")

if __name__=="__main__":
    clone_source()
    build_postgres()
    setup_database()
    setup_tpch()
    run_queries()
    print("\n Tested Tpch Dataset")
