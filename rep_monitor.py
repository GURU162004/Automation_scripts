import subprocess
import sys
import os
import time

HOME_DIR = os.path.expanduser("~")
INSTALL_PATH = os.path.join(HOME_DIR, "pgsql_replica")
bin_dir = os.path.join(INSTALL_PATH,"bin")
master_dir = os.path.join(INSTALL_PATH,"master_data")#Master data directory
slave_dir = os.path.join(INSTALL_PATH,"slave1_data")#Slave data directory
master_port = 5432
slave_port = 5433

def run_query(port, sql, single=False):
    cmd = f'{bin_dir}/psql -U postgres -p {port} -d postgres -t -c "{sql}"'
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    
def check_server_status(port):
    cmd = [os.path.join(bin_dir, "pg_isready"), "-p", str(port)]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

def monitor_loop():
    while True:
        master_up = check_server_status(master_port)
        slave_up = check_server_status(slave_port)
        print(f"\nMaster (Port: {master_port}): \n")
        if master_up:
            print("MASTER IS RUNNING")
            repl_sql = "SELECT client_addr, state, sent_lsn, write_lsn, replay_lsn FROM pg_stat_replication;"
            repl_info = run_query(master_port, repl_sql)
            if repl_info:
                print(f"Replication State: \n {repl_info}")
            else:
                print("No active replication connections found.")
        
        print(f"\nSlave (Port: {slave_port}): \n")
        if slave_up:
            print("SLAVE IS RUNNING")
            status = run_query(slave_port,"SELECT pg_is_in_recovery();")
            if status == 't':
                role = "Standby"
            else:
                role = "Read-Write (Promoted)"
        
            slave_sql = "SELECT status, received_lsn, latest_end_lsn FROM pg_stat_wal_receiver;"
            recv_info = run_query(slave_port, slave_sql)
            if recv_info:
                print(f"    WAL Receiver: {recv_info}")
        time.sleep(2)

if __name__=="__main__":
    monitor_loop()

