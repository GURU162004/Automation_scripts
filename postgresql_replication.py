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
log_dir = os.path.join(HOME_DIR,"pglogs")#Postgresql Master and Slave logs

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
    os.chdir(SOURCE_FOLDER)
    print("\n Configuring, Compiling and Installing PostgreSQL")
    run(f"./configure --prefix={INSTALL_PATH} --with-pgport=5432")
    run("make")
    run("make install")
    
def setup_master():
    print("\n Setting up Master")

    if os.path.exists(master_dir):
        status = subprocess.run(f"{bin_dir}/pg_ctl -D {master_dir} status", shell=True)
        if(status.returncode==0):
            run(f"{bin_dir}/pg_ctl -D {master_dir} -m fast stop")
    else:
        run(f"{bin_dir}/initdb -U postgres -D {master_dir}")

    pgconf = os.path.join(master_dir,"postgresql.conf")
    with open(pgconf,"a") as f:
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
    with open(pg_hba,"a") as f:
        f.write(f"host    replication    postgres    {SLAVE_IP}/32    trust\n")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    run(f"{bin_dir}/pg_ctl -D {master_dir} -l {log_dir}/master.log start")

def setup_slave(ctr :int):
    print("\n Setting up Slave")

    slave_dir = os.path.join(INSTALL_PATH,f"slave_data{ctr}")#Slave data
    if os.path.exists(slave_dir):
        status = subprocess.run(f"{bin_dir}/pg_ctl -D {slave_dir} status", shell=True)
        if(status.returncode==0):
            run(f"{bin_dir}/pg_ctl -D {slave_dir} -m fast stop")
        run(f"rm -rf {slave_dir}")
        
    slot_nm = f'slave_{ctr}'    
    run(f"{bin_dir}/pg_basebackup -U postgres -D {slave_dir} -h {MASTER_IP} -p 5432 -X stream -R -S {slot_nm}")
    port = 5432+ctr

    pgconf1 = os.path.join(slave_dir,"postgresql.conf")
    with open(pgconf1,"a") as f:
        f.write(f"\nport = {port}")
        if MASTER_IP == "127.0.0.1" and SLAVE_IP == "127.0.0.1":
            f.write(f"\nlisten_addresses = \'localhost\'")
        else:
            f.write(f"\nlisten_addresses = \'*\'")
        f.write(f"\nprimary_slot_name = '{slot_nm}'")
        f.write(f"\nhot_standby = on")
    run(f"chmod 700 {slave_dir}")

    print(f"\nStarting Slave {ctr} server...")
    run(f"{bin_dir}/pg_ctl -D {slave_dir} -l {log_dir}/slave{ctr}.log start")

def test_replication():
    run(f'{bin_dir}/psql -U postgres -p 5432 -d postgres -c "DROP DATABASE IF EXISTS repltest;"')
    run(f'{bin_dir}/psql -U postgres -p 5432 -d postgres -c "CREATE DATABASE repltest;"')
    
    test_sql = (
        " CREATE TABLE test_replication (id serial primary key, data text);"
        " INSERT INTO test_replication (data) VALUES ('row1'), ('row2');"
        " SELECT * FROM test_replication;"
    )
    cmd_master = f'{bin_dir}/psql -U postgres -p 5432 -d repltest -c "{test_sql}"'
    run(cmd_master)
    cmd_slave = f'{bin_dir}/psql -U postgres -p 5433 -d repltest -c "SELECT pg_is_in_recovery(), * FROM test_replication;"'
    run(cmd_slave)
    
if __name__=="__main__":
    clone_source()
    build_postgres()
    print("\n Postgresql Installed")
    c=0
    mf=0
    ctr=0
    while(True):
        print("\nEnter 1 : Setup Master")
        print("\nEnter 2 : Create and Setup Slave")
        print("\nEnter 3 : Exit")
        c = int(input("Enter Choice : "))
        if c==1 and mf==0:
            setup_master()
            print("Created Master and it is running...")
            mf=1
        elif c==2:
            ctr+=1
            setup_slave(ctr)
            print(f"Created Slave {ctr} and it is running...")
        else:
            break
    
    print("\n Configured Master Slave Replication Setup")

    print("Testing Master Slave setup..")
    test_replication()
    
    

