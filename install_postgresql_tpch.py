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

def run(command, cwd=None, shell=True):
    print(f"\n Running: {command}")
    try:
        subprocess.run(command, cwd=cwd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error executing command: {command}")
        print(f"[!] Reason: {e}")
        sys.exit(1)
    
def clone_source():
    if not os.path.exists(INSTALL_PATH):
        os.makedirs(INSTALL_PATH)
        print("\n git cloning repository ....")
        run(f"git clone {SOURCE_URL}")
    os.chdir(INSTALL_PATH)
    
    print("\n listing branches : ")
    os.chdir(SOURCE_FOLDER)
    run("git branch -r | grep REL")
    VERSION = input("Enter Version : ")
    run(f"git checkout REL_{VERSION}_STABLE")
          
def build_postgres():
    postgres_bin = os.path.join(BIN_DIR,"postgres")
    if os.path.exists(postgres_bin):
        print("\nPostgreSQL is already compiled and installed")
        return
    os.chdir(SOURCE_FOLDER)
    print("\n Configuring and Compiling ")
    run(f"./configure --prefix={INSTALL_PATH} --with-pgport=5433")
    run("make")
    run("make install")
    
def setup_database():
    print("\n Setting up Database")
    data_dir = os.path.join(INSTALL_PATH,"data")
    if not os.path.exists(data_dir):
        run(f"{BIN_DIR}/initdb -D {data_dir}")
    status = subprocess.run(f"{BIN_DIR}/pg_ctl -D {data_dir} status", shell=True)
    if(status.returncode!=0):
        print("\nPostgreSQL is not running. Starting server...")
        run(f"{BIN_DIR}/pg_ctl -D {data_dir} -l logfile start")
    else:
        print("\nPostgreSQL server is already running.")
    
def setup_tpch():
    if not os.path.exists(TPCH_DIR):
        print("\n git cloning repository ....")
        run(f"git clone {TPCH_URL}")
    else:
        print("\n tpch directory exists")
    os.chdir(os.path.join(TPCH_DIR,"dbgen"))
    run("make clean")
    run("make MACHINE=LINUX DATABASE=POSTGRESQL")
    run(f"{BIN_DIR}/createdb -p 5433 tpch")
    create_schema = "CREATE SCHEMA IF NOT EXISTS tpch;"
    run(f"{BIN_DIR}/psql -p 5433 -d tpch -c {create_schema}")
    run(f"{BIN_DIR}/psql -p 5433 -d tpch -f dss.ddl")
    
    for tbl in tables:
        file = f"{tbl}.tbl"
        sql = f"\copy {tbl} FROM '{file}' WITH (FORMAT csv, DELIMITER '|', NULL '')"
        run(f"{BIN_DIR}/psql -p 5433 -d tpch -c {sql}")
    
    run("cp -r queries queries_backup")
    run("git clone https://github.com/dhuny/tpch.git temp")
    run("cp temp/sample\ queries/*.sql queries/")
    run("rm -rf temp")

def run_queries():
    for i in range(1,23):
        qfile = str(i)+".sql"
        print(f"running {qfile} ...")
        start = time.time()
        run(F"{BIN_DIR}/pgsql -p 5433 -d tpch -f {TPCH_DIR}/dbgen/queries/{qfile}")
        end = time.time()
        run_time = end - start
        print(f"Query {qfile} executed in {run_time:.3f} seconds")
    
if __name__=="__main__":
    clone_source()
    build_postgres()
    setup_database()
    setup_tpch()
    run_queries()
    print("\n Postgresql installed successfully")
    
    

