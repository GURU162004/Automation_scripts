import subprocess
import os
import time

HOME_DIR = os.path.expanduser("~")
INSTALL_PATH = os.path.join(HOME_DIR, "pgsql_replica")
bin_dir = os.path.join(INSTALL_PATH,"bin")
master_dir = os.path.join(INSTALL_PATH,"master_data")#Master data directory
slave_dir = os.path.join(INSTALL_PATH,"slave_data1")#Slave data directory
newslave_dir = os.path.join(INSTALL_PATH,"slave_data2")
master_port = 5432
slave_port = 5433

def run_query(port, sql):
    cmd = f'{bin_dir}/psql -U postgres -p {port} -d postgres -c "{sql}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    
def check_server_status(port):
    result = subprocess.run(f"{bin_dir}/pg_isready -p {port}", capture_output=True, shell=True)
    return result.returncode == 0

def get_replicationstatus(port):
    repl_sql = "SELECT client_addr, state, write_lag, replay_lag FROM pg_stat_replication;"
    repl_info = run_query(port, repl_sql)
    return repl_info

def monitor_loop():
    while True:
        master_up = check_server_status(master_port)
        slave_up = check_server_status(slave_port)
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
            status = f'{bin_dir}/psql -U postgres -p {slave_port} -d postgres -t -A -c "SELECT pg_is_in_recovery();"'
            is_standby = subprocess.getoutput(status).strip()
            if is_standby == 't':
                print("Role: Standby")
                slave_sql = "SELECT sender_host, slot_name, status FROM pg_stat_wal_receiver;"
                recv_info = run_query(slave_port, slave_sql)
                if recv_info:
                    print(f"    WAL Receiver: \n {recv_info}")
            else:
                print("Role: Read-Write (Promoted)")
                srepl_info = get_replicationstatus(slave_port)
                if srepl_info:
                    print(f"Replication State: \n {srepl_info}")
                else:
                    print("No active replication connections found.")

        else:
            print("SLAVE IS NOT RUNNING")

        failover_path = os.path.join(HOME_DIR,"Automation_scripts")

        if not master_up and slave_up:
            status = f'{bin_dir}/psql -U postgres -p {slave_port} -d postgres -t -A -c "SELECT pg_is_in_recovery();"'
            is_standby = subprocess.getoutput(status).strip()
            if is_standby == "t":
                print("\nMaster DOWN. Slave is STANDBY.")
                subprocess.run("python3 rep_failover.py",shell=True,cwd=failover_path)

        elif master_up and not slave_up:
            print("\nSlave is DOWN.")
            subprocess.run("python3 rep_failover.py",shell=True,cwd=failover_path)

        time.sleep(2)

if __name__=="__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\nMonitor Stopped.")

