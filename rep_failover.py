import os
import time
import subprocess

HOME = os.path.expanduser("~")
INSTALL = os.path.join(HOME, "pgsql_replica")
bin_dir = os.path.join(INSTALL, "bin")
master_dir = os.path.join(INSTALL, "master_data")
slave_dir  = os.path.join(INSTALL, "slave_data1")
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
    status = subprocess.run(f"{bin_dir}/pg_isready -p {port}", capture_output=True)
    return status.returncode==0

def Is_standby(port):
    status = subprocess.run(f'{bin_dir}/psql -U postgres -p {port} -d postgres -t -c "SELECT ps_is_in_recovery();"')
    return status.returncode==0

def promote_slave():
    run(f"{bin_dir}/pg_ctl -D {slave_dir} promote")
    time.sleep(3)
    if not Is_standby(SLAVE_PORT):
        print(f"Slave on port {SLAVE_PORT} is now a Read-Write Master.")
    else:
        print("Failed to promote, Slave is still in recovery mode.")

def create_new_slave():
    slot_name = "slave_1"
    print("Dropping existing slot:", slot_name)
    drop_slot_sql = f"SELECT pg_drop_replication_slot('{slot_name}') WHERE EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = '{slot_name}');"
    run(f'{bin_dir}/psql -U postgres -p {MASTER_PORT} -d postgres -c "{drop_slot_sql}"')

    if os.path.exists(slave_dir):
        print("Removing old slave dir: ",slave_dir)
        run(f"rm -rf {slave_dir}")
        
    run(f"{bin_dir}/pg_basebackup -U postgres -D {slave_dir} -h {MASTER_IP} -p {MASTER_PORT} -X stream -R -C -S {slot_name}")
    run(f"chmod 700 {slave_dir}")

    alter = f'{bin_dir}/psql -U postgres -p {SLAVE_PORT} -d postgres -c "ALTER SYSTEM SET primary_slot_name = \'{slot_name}\';"'
    run(alter)
    run(f"{bin_dir}/pg_ctl -D {slave_dir} restart")
    time.sleep(3)
    print("New slave created and started, using slot:", slot_name)

if __name__ == "__main__":
    master_up = Is_running(MASTER_PORT)
    slave_up = Is_running(SLAVE_PORT)
    if not master_up and slave_up:
        print("Master down & Slave up ---> Promote slave to master.")
        promote_slave()
    elif master_up and not slave_up:
        print("Slave down & Master up ---> Create new Slave")
        create_new_slave() 


    
