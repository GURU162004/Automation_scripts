import subprocess
import os
import time

HOME_DIR = os.path.expanduser("~")
INSTALL_PATH = os.path.join(HOME_DIR, "pgsql_replica")
bin_dir = os.path.join(INSTALL_PATH,"bin")
master_dir = os.path.join(INSTALL_PATH,"master_data")#Master data directory
slave_dir = os.path.join(INSTALL_PATH,"slave_data1")#Slave data directory
newslave_dir = os.path.join(INSTALL_PATH,"slave_data2")
script_path = os.path.join(HOME_DIR,"Automation_scripts")#script path
master_port = 5432
slave_port = 5433

def run_query(port, sql):
    cmd = f'{bin_dir}/psql -U postgres -p {port} -d postgres -c "{sql}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    
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
                subprocess.run("python3 rep_failover.py",shell=True,cwd=script_path)#calls the failover script when the Master server is down

        elif master_up and not slave_up:
            print("\nSlave is DOWN.")#calls the failover script when the Slave server is down
            subprocess.run("python3 rep_failover.py",shell=True,cwd=script_path)

        time.sleep(2)

if __name__=="__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\nMonitor Stopped.")

