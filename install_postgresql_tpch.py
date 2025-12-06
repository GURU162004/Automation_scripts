import subprocess
import sys
import os
import time
import csv

DIR_NAME = "pgsql_git"
SOURCE_URL = "https://github.com/postgres/postgres.git" 
TPCH_URL = "https://github.com/gregrahn/tpch-kit.git"

HOME_DIR = os.path.expanduser("~") 
INSTALL_PATH = os.path.join(HOME_DIR, DIR_NAME)
SOURCE_FOLDER = os.path.join(INSTALL_PATH, "postgres")
TPCH_DIR = os.path.join(HOME_DIR, "tpch_kit")
DATA_DIR = os.path.join(INSTALL_PATH,"data")
BIN_DIR = os.path.join(INSTALL_PATH,"bin")

tables = ["customer","lineitem","nation","orders","part","partsupp","region","supplier"]#TPC-H dataset tables

def run(command, cwd=None, shell=True, quiet=False):
    print(f"\n Running: {command}")
    try:
        if quiet:#Hides the shell output to make the shell interface clean
            subprocess.run(command, cwd=cwd, shell=shell, check = True, stdout = subprocess.DEVNULL)
        else:
            subprocess.run(command, cwd=cwd, shell=shell, check = True)
    except subprocess.CalledProcessError as e:#if the cmd execution fails the error is captured and printed
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
    run("git branch -r | grep REL",cwd=SOURCE_FOLDER)#Lists all the versions of PostgreSQL in the remote branches
    VERSION = input("Enter Version : ")
    run(f"git checkout REL_{VERSION}_STABLE",cwd=SOURCE_FOLDER)#Switches to the preferred version
          
def build_postgres():
    postgres_bin = os.path.join(BIN_DIR,"postgres")
    if os.path.exists(postgres_bin):#Bin directory is created when the source is compiled and installed
        print("\nPostgreSQL is already compiled and installed")
        return
    print("\n Configuring and Compiling ")
    run(f"./configure --prefix={INSTALL_PATH} --with-pgport=5433",cwd=SOURCE_FOLDER)#Configured to install in a custom folder in home and run at port 5433
    run("make",cwd=SOURCE_FOLDER)#Compiles and builds the source
    run("make install",cwd=SOURCE_FOLDER)#Installs PostgreSQL from source
    
def setup_database():
    print("\n Setting up Database")
    data_dir = os.path.join(INSTALL_PATH,"data")#PostgreSQL database directory
    if not os.path.exists(data_dir):
        run(f"{BIN_DIR}/initdb -D {data_dir}")#Initializes the database and creates a data directory
    status = subprocess.run(
        f"{BIN_DIR}/pg_ctl -D {data_dir} status",#To check if the PostgreSQL server is running or not.
        shell=True,
        stdout=subprocess.DEVNULL,#To hide the output of the command
        stderr=subprocess.DEVNULL,#To hide the error of the command
    )
    if(status.returncode!=0):
        print("\nPostgreSQL is not running. Starting server...")
        run(f"{BIN_DIR}/pg_ctl -D {data_dir} -l logfile start")#If not running, the server is started and output id logged to the logfile
    else:
        print("\nPostgreSQL server is already running.")
    
def setup_tpch():
    if not os.path.exists(TPCH_DIR):
        print("\n git cloning repository ...")
        run(f"git clone {TPCH_URL} {TPCH_DIR}")#TPC-H dataset repository
    else:
        print("\n tpch directory exists")
    dbgen_dir = os.path.join(TPCH_DIR,"dbgen")
    run("make clean",cwd=dbgen_dir,quiet=True)#Cleans built files from source
    run("make MACHINE=LINUX DATABASE=POSTGRESQL",cwd=dbgen_dir,quiet=True)#Sets to Linux OS and PostgreSQL db in the Makefile, compiles and builds

    if not os.path.exists(os.path.join(TPCH_DIR,"dbgen","supplier.tbl")):#Checks if datasets exists
        print("\nGenerating TPC-H data (scale factor 1) ...")
        run("./dbgen -s 1",cwd=dbgen_dir)#Generates TPC-H datasets at a scale 1GB in the /dbgen directory
    else:
        print("\nTPC-H data already exists, skipping dbgen")

    run(f"{BIN_DIR}/dropdb -p 5433 --if-exists tpch",cwd=dbgen_dir)#Drops the tpch database if it already exists on port 5433
    run(f"{BIN_DIR}/createdb -p 5433 tpch",cwd=dbgen_dir)#Creates a database to run on port 5433 with name tpch
    run(f"{BIN_DIR}/psql -p 5433 -d tpch -f dss.ddl",cwd=dbgen_dir)#Creates tables and structure for the TPC-H database from the dss.ddl(Data Definition Language(DDL) file)
    
    for tbl in tables:
        file = f"{tbl}.tbl"
        sql = f"\\copy {tbl} FROM '{file}' WITH (FORMAT csv, DELIMITER '|', NULL '')"
        run(f'{BIN_DIR}/psql -p 5433 -d tpch -c "{sql}"',cwd=dbgen_dir)#Copies the dataset from the table files in csv format to the TPC-H database
    
    run("cp -r queries queries_backup",cwd=dbgen_dir)#copies the queries to the queries_backup folder
    run("git clone https://github.com/dhuny/tpch.git temp",cwd=dbgen_dir)#clones TPC-H sql queries to temp folder
    run("cp temp/sample\ queries/*.sql queries/",cwd=dbgen_dir)#copies temp/sample queries/*.sql files to queries folder
    run("rm -rf temp",cwd=dbgen_dir)

def run_queries():
    results_csv = "tpch_results.csv"
    csv_path = os.path.join(TPCH_DIR,results_csv)
    
    if os.path.exists(csv_path):
        os.remove(csv_path)

    with open(csv_path, "w", newline="") as results_csv:#Creates and opens the results.csv file in write mode
        header = ["Query","Trial1_Time(ms)","Trial2_Time(ms)","Trial3_Time(ms)","Average_Time(ms)"]#Fields of the results
        writer = csv.writer(results_csv)
        writer.writerow(header)#Writes the fields headings
        for i in range(1,23):
            qfile = f"{i}.sql"
            run_times = []
            for r in range(3):
                print(f"Trial {r+1}: Query {qfile} executing...")
                cmd = f'{BIN_DIR}/psql -p 5433 -q -t -d tpch -c "\\timing on" -f {TPCH_DIR}/dbgen/queries/{qfile} | grep "Time:"'#Runs each query files and pipes only the Time output
                res = subprocess.run(cmd,shell=True,check=True,text=True,stdout = subprocess.PIPE,stderr=subprocess.STDOUT)#Runs and captures the result
                output = res.stdout.split(' ')
                run_time = float(output[1])#Extracts the time value from the Time: output in float data type
                run_times.append(run_time)
                print(f'Time: {run_time:.2f} ms')
            avg = (run_times[0] + run_times[1] + run_times[2])/3.0
            print(f"The Average Execution time of the Query {qfile} is {avg:.2f} ms")
            writer.writerow([qfile] + run_times + [avg])#writes records for each query
    print(f"\nResults saved to: {results_csv}")

if __name__=="__main__":
    clone_source()
    build_postgres()
    setup_database()
    setup_tpch()
    run_queries()
    print("\n Tested TPC-H Dataset benchmark")
