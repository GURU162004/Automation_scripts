import subprocess
import sys
import os
import time

DIR_NAME = "pgsql_replica"
SOURCE_URL = "https://github.com/postgres/postgres.git"

HOME_DIR = os.path.expanduser("~")
INSTALL_PATH = os.path.join(HOME_DIR, DIR_NAME)
SOURCE_FOLDER = os.path.join(INSTALL_PATH, "postgres")
bin_dir = os.path.join(INSTALL_PATH,"bin")
master_dir = os.path.join(INSTALL_PATH,"master_data")#Master data directory
log_dir = os.path.join(HOME_DIR,"pglogs")#Postgresql Master and Slave logs
vfile = os.path.join(INSTALL_PATH,"version.txt")

MASTER_IP = "127.0.0.1" #MASTER_IP_Address DEFAULT local host
SLAVE_IP = "127.0.0.1" #SLAVE_IP_Address DEFAULT local host

def run(command, cwd=None, shell=True, env=None):
    print(f"\n Running: {command}")
    try:
        subprocess.run(command, cwd=cwd, shell=shell, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"\nError executing command: {command}")
        print(f"Reason: {e}")
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
    VERSION = input("Enter PostgreSQL Version : ")
    run(f"git checkout REL_{VERSION}_STABLE")
    build_postgres(VERSION)
          
def build_postgres(VERSION : str):
    postgres_bin = os.path.join(bin_dir,"postgres")
    v = VERSION
    if os.path.exists(vfile):
        with open(vfile,"r") as f:#reads the version from the version file created after installation
            v = f.read().strip()
        run(f"rm -rf {vfile}")
    if os.path.exists(postgres_bin) and v==VERSION:#Postgresql is installed when the postgres bin directory is present and it is same as the specified version
        print("\nPostgreSQL is already compiled and installed")
        return
    os.chdir(SOURCE_FOLDER)#Otherwise, the PostgreSQL is installed
    print("\n Configuring, Compiling and Installing PostgreSQL")
    run(f"./configure --prefix={INSTALL_PATH} --with-pgport=5432")#Configured to install in a custom folder in home and run at port 5432
    run("make")#Compiles and builds the source
    run("make install")#Installs Postgres from the source.
    with open(vfile,"w") as f:
        f.write(VERSION)
    
def setup_master():
    print("\n Setting up Master")
    if os.path.exists(master_dir):
        status = subprocess.run(f"{bin_dir}/pg_ctl -D {master_dir} status", shell=True)
        if(status.returncode==0):#Checks if Master server is running, if running, cmd exit return code is 0
            run(f"{bin_dir}/pg_ctl -D {master_dir} -m fast stop")#If running, Master server stopped
        run(f"rm -rf {master_dir}")#removes previous master if exists
    run(f"{bin_dir}/initdb -U postgres -D {master_dir}")#Initializes the Master with common user postgres 

    pgconf = os.path.join(master_dir,"postgresql.conf")
    with open(pgconf,"a") as f:
        f.write(f"\nport = 5432")#Sets Master server port
        if MASTER_IP == "127.0.0.1" and SLAVE_IP == "127.0.0.1":#Checks the IPs are local host or not
            f.write(f"\nlisten_addresses = \'localhost\'")#If yes, sets listen addresses to local host
        else:
            f.write(f"\nlisten_addresses = \'*\'")#else, sets the listening addresses to * to listen all IPv4s
        f.write(f"\nwal_level = replica")#Provides enough information to support WAL archiving and streaming replication, including running read-only queries on a standby server. 
        f.write(f"\nmax_wal_senders = 10")#Set according to number of slaves required, default 10
        f.write(f"\nwal_keep_size = 1024")#Minimum amount of WAL(Write Ahead Log) data to retain in the pg_wal directory of Master in Mb
        f.write(f"\nmax_replication_slots = 10")#Set according to number of slaves required, default 10

    pg_hba = os.path.join(master_dir,"pg_hba.conf")
    with open(pg_hba,"a") as f:#Opens the host based authentication file.
        f.write(f"host    replication    postgres    {SLAVE_IP}/32    trust\n")#Sets the host and connection to replication, user: postgres, SLAVE IP and sets no password authentication(trust)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    run(f"{bin_dir}/pg_ctl -D {master_dir} -l {log_dir}/master.log start")#Starts the master server and logs

def setup_slave(ctr :int):
    print("\n Setting up Slave")
    slot_nm = f'slave_{ctr}'  
    slave_dir = os.path.join(INSTALL_PATH,f"slave_data{ctr}")#Slave data directory
    
    if os.path.exists(slave_dir):
        status = subprocess.run(f"{bin_dir}/pg_ctl -D {slave_dir} status", shell=True)
        if(status.returncode==0):
            run(f"{bin_dir}/pg_ctl -D {slave_dir} -m fast stop")
        run(f"{bin_dir}/psql -U postgres -p 5432 -d postgres -c \"SELECT pg_drop_replication_slot('{slot_nm}') WHERE EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = '{slot_nm}');\"")
        #Drops the replication slot, if the slot exists in the table pg_replication_slots
        run(f"rm -rf {slave_dir}")

    run(f"{bin_dir}/pg_basebackup -U postgres -D {slave_dir} -h {MASTER_IP} -p 5432 -X stream -R -C -S {slot_nm}") #Backups the Master data to the new Slave data 
    #-X stream : Streams the WAL records during backup to avoid data loss during backup process
    #-R : Creates Standby.signal on the slave data and auto configures the connection settings of the master to the slave server.
    #-C -S Creates a new slot with the given name
    #Replication slots acts like a queue or a buffer that store the wal files until it is confirmed that slave received them.
    
    port = 5432+ctr

    pgconf1 = os.path.join(slave_dir,"postgresql.conf")
    with open(pgconf1,"a") as f:
        f.write(f"\nport = {port}")
        if MASTER_IP == "127.0.0.1" and SLAVE_IP == "127.0.0.1":#Checks the connection is local host or not.
            f.write(f"\nlisten_addresses = \'localhost\'")#Sets to local host 
        else:
            f.write(f"\nlisten_addresses = \'*\'")#Sets to accept any IPv4 addresses
        f.write(f"\nprimary_slot_name = '{slot_nm}'")#Configures the slot created
        f.write(f"\nhot_standby = on")#Allows replica to accept read only queries and connect to primary server
    run(f"chmod 700 {slave_dir}")#Sets read, write and execute permissions to user of the slave data

    print(f"\nStarting Slave {ctr} server...")
    run(f"{bin_dir}/pg_ctl -D {slave_dir} -l {log_dir}/slave{ctr}.log start")

def test_replication():
    run(f'{bin_dir}/psql -U postgres -p 5432 -d postgres -c "DROP DATABASE IF EXISTS repltest;"')#drops the repltest db if it exists
    run(f'{bin_dir}/psql -U postgres -p 5432 -d postgres -c "CREATE DATABASE repltest;"')#creates new repltest db
    test_sql = (
        " CREATE TABLE test_replication (id serial primary key, data text);"
        " INSERT INTO test_replication (data) VALUES ('row1'), ('row2');"
        " SELECT * FROM test_replication;"
    )
    cmd_master = f'{bin_dir}/psql -U postgres -p 5432 -d repltest -c "{test_sql}"' #Runs on Master, Creates table and adds data in the repltest database
    run(cmd_master)
    catchup_lag(5433)
    cmd_slave = f'{bin_dir}/psql -U postgres -p 5433 -d repltest -c "SELECT pg_is_in_recovery(), * FROM test_replication;"' #Runs on Slave, Reads the table created in the Master in repltest database
    run(cmd_slave)

def catchup_lag(slave_port : int):
    while True:
        cmd_master = (f'{bin_dir}/psql -U postgres -p 5432 -d postgres -t -c "SELECT pg_current_wal_lsn();"')
        master_lsn = subprocess.getoutput(cmd_master).strip()#LSN of the WAL record written on the cache memory of the master at the time it was called
        cmd_standby = (f'{bin_dir}/psql -U postgres -p {slave_port} -d postgres -t -c "SELECT pg_last_wal_replay_lsn();"')
        standby_lsn = subprocess.getoutput(cmd_standby).strip()#LSN of the most recent WAL record that has been applied on Slave
        print(f"  master_lsn={master_lsn}, standby_replay_lsn={standby_lsn}")
        if master_lsn == standby_lsn and master_lsn not in ("", "(null)"):
            print("Slave has replayed WAL record up to Master's current LSN.")
            break
        time.sleep(2)

if __name__=="__main__":
    clone_source()
    print("\n Postgresql Installed")
    c=0#choice
    mf=0#Master_flag
    ctr=0#Slaves counter
    while(True):
        print("\nEnter 1 : Setup Master")
        print("\nEnter 2 : Create and Setup Slave")
        print("\nEnter 3 : Exit")
        c = int(input("\nEnter Choice : "))
        if c==1 and mf==0:
            setup_master()
            print("Created Master and it is running...")
            mf=1#Flag to create only one Master
        elif c==2:
            ctr+=1
            setup_slave(ctr)    
            print(f"Created Slave {ctr} and it is running...")
        else:
            break
    
    print("\n Configured Master Slave Replication Setup")
    print("Testing Single Master Slave setup..")
    test_replication()
    
    

