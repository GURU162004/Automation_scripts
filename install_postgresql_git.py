import subprocess
import sys
import os
import requests

DIR_NAME = "pgsql_git"
SOURCE_URL = "https://github.com/postgres/postgres.git"
VERSION = 18

HOME_DIR = os.path.expanduser("~")
INSTALL_PATH = os.path.join(HOME_DIR, DIR_NAME)
SOURCE_FOLDER = os.path.join(INSTALL_PATH, f"postgres")

def run(command, cwd=None, shell=True):
    print(f"\n Running: {command}")
    try:
        subprocess.run(command, cwd=cwd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error executing command: {command}")
        print(f"[!] Reason: {e}")
        sys.exit(1)
    
def clone_source():
    if not os.path.exists(INSTALL_PATH):
        os.makedirs(INSTALL_PATH)
    os.chdir(INSTALL_PATH)
    print("\n git cloning repository ....")
    run(f"git clone {SOURCE_URL}")
    
    print("\n listing branches : ")
    os.chdir(SOURCE_FOLDER)
    run("git branch -r | grep REL")
    run(f"git checkout REL_{VERSION}_STABLE")
          
def build_postgres():
    os.chdir(SOURCE_FOLDER)
    print("\n Configuring and Compiling ")
    run(f"./configure --prefix={INSTALL_PATH}")
    run("make")
    run("make install")
    
def setup_database():
    print("\n Setting up Database")
    data_dir = os.path.join(INSTALL_PATH,f"data")
    bin_dir = os.path.join(INSTALL_PATH,f"bin")
    if not os.path.exists(data_dir):
        run(f"{bin_dir}/initdb -D {data_dir}")
    run(f"{bin_dir}/pg_ctl -D {data_dir} -l logfile start")
    run(f"{bin_dir}/createdb test")
    
if __name__=="__main__":
    clone_source()
    build_postgres()
    setup_database()
    print("\n Postgresql installed successfully")
    
    

