import os
import time
import subprocess

HOME = os.path.expanduser("~")
INSTALL = os.path.join(HOME, "pgsql_replica")
bin_dir = os.path.join(INSTALL, "bin")
master_dir = os.path.join(INSTALL, "master_data")
oldslave_dir = os.path.join(INSTALL, "slave_data1")
newslave_dir = os.path.join(INSTALL, "slave_data2")
log_dir = os.path.join(HOME,"pglogs")
MASTER_PORT = 5432
SLAVE_PORT  = 5433
MASTER_IP = "127.0.0.1"

def run(command, shell=True):
    print(f"\n Running: {command}")
    try:
        subprocess.run(command, shell=shell, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError executing command: {command}")
        print(f"Reason: {e}")
        return False

def Is_running(port):
    status = subprocess.run(f"{bin_dir}/pg_isready -U postgres -p {port}", capture_output=True, shell=True)#Checks postgresql server running or not.
    return status.returncode==0 #if the server is running then return code is 0 else the return code is 2

def Is_standby(port):
    status = subprocess.run(f'{bin_dir}/psql -U postgres -p {port} -d postgres -t -c "SELECT pg_is_in_recovery();"', capture_output=True, shell=True)#If the slave is standby(read-only) then returns t(true)
    return status.stdout.strip().decode() == 't' #extract the result of pg is in recovery

def promote_slave():
    run(f"{bin_dir}/pg_ctl -D {newslave_dir} promote") 
    #Slave stops listening to Wal records from Master, Standby.signal is deleted. Slave becomes Master(Read/Write)
    time.sleep(5)
    if not Is_standby(SLAVE_PORT):
        print(f"Slave on port {SLAVE_PORT} is now a Read-Write Master.")

def create_new_slave():
    slot_name = "slave_new"#new slot
    slot_nm = "slave_1"#old slot name
    print("Dropping existing slot:", slot_name)
    drop_slot_sql = f"SELECT pg_drop_replication_slot('{slot_name}') WHERE EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = '{slot_nm}');" #Drops the slot if the slot exists in the pg_replication_slots table
    run(f'{bin_dir}/psql -U postgres -p {MASTER_PORT} -d postgres -c "{drop_slot_sql}"')

    if os.path.exists(oldslave_dir):
        print("Removing old slave dir: ",oldslave_dir)
        run(f"rm -rf {oldslave_dir}")
        
    run(f"{bin_dir}/pg_basebackup -U postgres -D {newslave_dir} -h {MASTER_IP} -p {MASTER_PORT} -X stream -R -C -S {slot_name}")#Backups the Master data to the new Slave data 
    #-X stream : Streams the WAL records during backup to avoid data loss during backup process
    #-R : Creates Standby.signal on the slave data and auto configures the connection settings of the master in the postgresql.
    #-C -S Creates a new slot with the given name
    #Replication slots acts like a queue or a buffer that store the wal files until it is confirmed that slave received them.

    run(f"chmod 700 {newslave_dir}")#Modifies to Read, Write and Execute permissions for the slave data

    pgconf1 = os.path.join(newslave_dir,"postgresql.conf")
    with open(pgconf1,"a") as f:
        f.write(f"\nport = {SLAVE_PORT}")#updates the new slave port
        f.write(f"\nprimary_slot_name = '{slot_name}'")#configures the slot name created

    run(f"{bin_dir}/pg_ctl -D {newslave_dir} -l {log_dir}/slavenew.log start")#starts the new slave
    time.sleep(3)
    print("New slave created and started, using slot:", slot_name)

if __name__ == "__main__":
    master_up = Is_running(MASTER_PORT)
    slave_up = Is_running(SLAVE_PORT)
    if not master_up and slave_up:
        print("Promoting slave to master.")
        promote_slave()
    elif master_up and not slave_up:
        print("Creating new Slave")
        create_new_slave() 


    
