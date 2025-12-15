import os
import time
import subprocess

HOME = os.path.expanduser("~")
INSTALL_PATH = os.path.join(HOME, "pgsql_replica")
bin_dir = os.path.join(INSTALL_PATH,"bin")
master_dir = os.path.join(INSTALL_PATH,"master_data")#Master data directory
slave_dir = os.path.join(INSTALL_PATH,"slave_data1")#Slave data directory
newslave_dir = os.path.join(INSTALL_PATH,"slave_data2")
script_path = os.path.join(HOME,"Automation_scripts")#script path
log_dir = os.path.join(HOME,"pglogs")
master_port = 5432
slave_port = 5433
MASTER_IP = "127.0.0.1"

def run_query(port, sql):
    cmd = f'{bin_dir}/psql -U postgres -p {port} -d postgres -c "{sql}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    
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
    result = subprocess.run(f"{bin_dir}/pg_isready -p {port}", capture_output=True, shell=True)#Checks postgresql server running or not.
    return result.returncode == 0 #if the server is running then return code is 0 else the return code is 2

def Is_standby(port):
    status = subprocess.run(f'{bin_dir}/psql -U postgres -p {port} -d postgres -t -c "SELECT pg_is_in_recovery();"', capture_output=True, shell=True)#If the slave is standby(read-only) then returns t(true)
    return status.stdout.strip().decode() == 't' #extract the result of pg is in recovery

def get_replicationstatus(port):
    repl_sql = "SELECT pid, client_addr, state FROM pg_stat_replication;" #Master server displays process id, client address and state information
    repl_info = run_query(port, repl_sql)
    return repl_info

def promote_slave():
    run(f"{bin_dir}/pg_ctl -D {newslave_dir} promote") 
    #Slave stops listening to Wal records from Master, Standby.signal is deleted. Slave becomes Master(Read/Write)
    time.sleep(5)
    if not Is_standby(slave_port):
        print(f"Slave on port {slave_port} is now a Read-Write Master.")

def create_new_slave():
    slot_name = "slave_new"#new slot
    slot_nm = "slave_1"#old slot name
    print("Dropping existing slot:", slot_name)
    drop_slot_sql = f"SELECT pg_drop_replication_slot('{slot_name}') WHERE EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = '{slot_nm}');" #Drops the slot if the slot exists in the pg_replication_slots table
    run(f'{bin_dir}/psql -U postgres -p {master_port} -d postgres -c "{drop_slot_sql}"')

    if os.path.exists(slave_dir):
        print("Removing old slave dir: ",slave_dir)
        run(f"rm -rf {slave_dir}")
        
    run(f"{bin_dir}/pg_basebackup -U postgres -D {newslave_dir} -h {MASTER_IP} -p {master_port} -X stream -R -C -S {slot_name}")#Backups the Master data to the new Slave data 
    #-X stream : Streams the WAL records during backup to avoid data loss during backup process
    #-R : Creates Standby.signal on the slave data and auto configures the connection settings of the master in the postgresql.
    #-C -S Creates a new slot with the given name
    #Replication slots acts like a queue or a buffer that store the wal files until it is confirmed that slave received them.

    run(f"chmod 700 {newslave_dir}")#Modifies to Read, Write and Execute permissions for the slave data

    pgconf1 = os.path.join(newslave_dir,"postgresql.conf")
    with open(pgconf1,"a") as f:
        f.write(f"\nport = {slave_port}")#updates the new slave port
        f.write(f"\nprimary_slot_name = '{slot_name}'")#configures the slot name created

    run(f"{bin_dir}/pg_ctl -D {newslave_dir} -l {log_dir}/slavenew.log start")#starts the new slave
    time.sleep(3)
    print("New slave created and started, using slot:", slot_name)

def monitor_loop():
    while True:
        master_up = Is_running(master_port)#checks whether master is running or not
        slave_up = Is_running(slave_port)#checks whether slave is runnning or not
        print(f"\nMaster (Port: {master_port}): \n")

        if master_up:
            print("MASTER IS RUNNING")
            repl_info = get_replicationstatus(master_port)
            if repl_info:
                print(f"Replication State: \n {repl_info}")
            else:
                print("No active replication connections found.")
        else:
            print("MASTER IS NOT RUNNING")
        print(f"\nSlave (Port: {slave_port}): \n")

        if slave_up:
            print("SLAVE IS RUNNING")
            status = f'{bin_dir}/psql -U postgres -p {slave_port} -d postgres -t -A -c "SELECT pg_is_in_recovery();"'#If the slave is standby(read-only) then returns t(true)
            is_standby = subprocess.getoutput(status).strip()#extract the result of pg is in recovery
            if is_standby(slave_port) == 't':
                print("Role: Standby")
                slave_sql = "SELECT pid, sender_host, slot_name, status FROM pg_stat_wal_receiver;"#display wal receiver stats such as pid, sender host, slot name, status for Slave
                recv_info = run_query(slave_port, slave_sql)
                if recv_info:
                    print(f"    WAL Receiver: \n {recv_info}")
            else:
                print("Role: Read-Write (Promoted)")
                srepl_info = get_replicationstatus(slave_port)#display replication stats when the slave is promoted 
                if srepl_info:
                    print(f"Replication State: \n {srepl_info}")
                else:
                    print("No active replication connections found.")
        else:
            print("SLAVE IS NOT RUNNING")

        if not master_up and slave_up:
            if is_standby(slave_port) == "t":
                print("\nMaster DOWN. Slave is STANDBY.")
                promote_slave()

        elif master_up and not slave_up:
            print("\nSlave is DOWN.")
            create_new_slave()

        time.sleep(2)

if __name__=="__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\nMonitor Stopped.")

