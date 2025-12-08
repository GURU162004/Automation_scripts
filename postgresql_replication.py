import subprocess
import sys
import os

DIR_NAME = "pgsql_replica"
SOURCE_URL = "https://github.com/postgres/postgres.git"

HOME_DIR = os.path.expanduser("~")
INSTALL_PATH = os.path.join(HOME_DIR, DIR_NAME)
SOURCE_FOLDER = os.path.join(INSTALL_PATH, "postgres")
bin_dir = os.path.join(INSTALL_PATH,"bin")
master_dir = os.path.join(INSTALL_PATH,"master_data")#Master data
slave_dir = os.path.join(INSTALL_PATH,"slave_data")#Slave data
log_dir = os.path.join(HOME_DIR,"pglogs")#Postgresql Master and Slave logs

SU_PASSWORD = "supass" #Super user password
RU_PASSWORD = "repass" #replication user password
MASTER_IP = "127.0.0.1" #MASTER_IP_Address DEFAULT local host
SLAVE_IP = "127.0.0.1" #SLAVE_IP_Address DEFAULT local host

def run(command, cwd=None, shell=True, env=None):
    print(f"\n Running: {command}")
    try:
        subprocess.run(command, cwd=cwd, shell=shell, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error executing command: {command}")
        print(f"[!] Reason: {e}")
        sys.exit(1)
    
def clone_source():
    if not os.path.exists(INSTALL_PATH):
        os.makedirs(INSTALL_PATH)
    os.chdir(INSTALL_PATH)
    if not os.path.exists(SOURCE_FOLDER):
        print("\n git cloning postgresql repository ...")
        run(f"git clone {SOURCE_URL}")
    
    print("\n listing branches : ")
    os.chdir(SOURCE_FOLDER)
    run("git branch -r | grep REL")
    VERSION = input("Enter Version : ")
    run(f"git checkout REL_{VERSION}_STABLE")
          
def build_postgres():
    postgres_bin = os.path.join(bin_dir,"postgres")
    if os.path.exists(postgres_bin):
        print("\nPostgreSQL is already compiled and installed")
        return
    os.chdir(SOURCE_FOLDER)
    print("\n Configuring, Compiling and Installing PostgreSQL")
    run(f"./configure --prefix={INSTALL_PATH} --with-pgport=5432")
    run("make")
    run("make install")
    
def setup_master():
    print("\n Setting up Master")

    pwfile = os.path.join(INSTALL_PATH, "master_pw.txt")
    with open(pwfile, "w", encoding="utf-8") as f:
        f.write(SU_PASSWORD + "\n")
    run(f"chmod 600 {pwfile}")

    if os.path.exists(master_dir):
        status = subprocess.run(f"{bin_dir}/pg_ctl -D {master_dir} status", shell=True)
        if(status.returncode==0):
            run(f"{bin_dir}/pg_ctl -D {master_dir} -m fast stop")
        run(f"rm -rf {master_dir}")

    run(f"{bin_dir}/initdb -D {master_dir} -U postgres -A scram-sha-256 --pwfile={pwfile}")

    pgconf = os.path.join(master_dir,"postgresql.conf")
    with open(pgconf,"a",encoding="utf-8") as f:
        f.write(f"\nport = 5432")
        if MASTER_IP == "127.0.0.1" and SLAVE_IP == "127.0.0.1":
            f.write(f"\nlisten_addresses = \'localhost\'")
        else:
            f.write(f"\nlisten_addresses = \'*\'")
        f.write(f"\nwal_level = replica")
        f.write(f"\nmax_wal_senders = 10")
        f.write(f"\nwal_keep_size = 1000")
        f.write(f"\nmax_replication_slots = 10")

    pg_hba = os.path.join(master_dir,"pg_hba.conf")
    with open(pg_hba,"a", encoding="utf-8") as f:
        f.write(f"host    replication    repuser    {SLAVE_IP}/32    scram-sha-256\n")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    run(f"{bin_dir}/pg_ctl -D {master_dir} -l {log_dir}/master.log start")

    env = os.environ.copy()
    env["PGPASSWORD"] = SU_PASSWORD
    run(f'{bin_dir}/psql -U postgres -p 5432 -d postgres -c "CREATE ROLE repuser WITH REPLICATION LOGIN PASSWORD \'{RU_PASSWORD}\';"',env=env)

def setup_slave():
    print("\n Setting up Slave")
    env = os.environ.copy()
    env["PGPASSWORD"] = RU_PASSWORD

    if os.path.exists(slave_dir):
        status = subprocess.run(f"{bin_dir}/pg_ctl -D {slave_dir} status", shell=True)
        if(status.returncode==0):
            run(f"{bin_dir}/pg_ctl -D {slave_dir} -m fast stop")
        run(f"rm -rf {slave_dir}")

    run(f"{bin_dir}/pg_basebackup -D {slave_dir} -U repuser -h {MASTER_IP} -p 5432 -Fp -Xs -P -R",env=env)
    pgconf1 = os.path.join(slave_dir,"postgresql.conf")

    with open(pgconf1,"a",encoding="utf-8") as f:
        f.write(f"\nport = 5433")
        f.write(f"\nlisten_addresses = \'localhost\'")
        f.write(f"\nhot_standby = on")
    run(f"chmod 700 {slave_dir}")

    print("\nStarting Slave server...")
    run(f"{bin_dir}/pg_ctl -D {slave_dir} -l {log_dir}/slave.log start")

def test_replication():
    env = os.environ.copy()
    env["PGPASSWORD"] = SU_PASSWORD

    run(f'{bin_dir}/psql -U postgres -p 5432 -d postgres -c "CREATE DATABASE repltest;"',env=env)
    
    test_sql = (
        " CREATE TABLE test_replication (id serial primary key, data text);"
        " INSERT INTO test_replication (data) VALUES ('row1'), ('row2');"
        " SELECT * FROM test_replication;"
    )
    cmd_master = f'{bin_dir}/psql -U postgres -p 5432 -d repltest -c "{test_sql}"'
    run(cmd_master,env=env)
    cmd_slave = f'{bin_dir}/psql -U postgres -p 5433 -d repltest -c "SELECT pg_is_in_recovery(), * FROM test_replication;"'
    run(cmd_slave,env=env)
    
if __name__=="__main__":
    clone_source()
    build_postgres()
    setup_master()
    setup_slave()
    print("\n Postgresql installed and configured Master Slave Replication Setup")
    print("Testing Master Slave setup")
    test_replication()
    
    

