import subprocess
import sys
import os
import requests

DIR_NAME = "pgsql"
SOURCE_URL = "https://ftp.postgresql.org/pub/source/v18.1/postgresql-18.1.tar.bz2"

HOME_DIR = os.path.expanduser("~")
INSTALL_PATH = os.path.join(HOME_DIR, DIR_NAME)
SOURCE_FOLDER = os.path.join(INSTALL_PATH, f"postgresql-18.1")

def run(command, cwd=None, shell=True):
    print(f"\n Running: {command}")
    try:
        subprocess.run(command, cwd=cwd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error executing command: {command}")
        print(f"[!] Reason: {e}")
        sys.exit(1)
    
def download_source():
    if not os.path.exists(INSTALL_PATH):
        os.makedirs(INSTALL_PATH)
    os.chdir(INSTALL_PATH)
    
    print("\n Downloading source zip file: ")
    response = requests.get(SOURCE_URL)
    file_path = os.path.join(INSTALL_PATH,f"postgresql-18.1.tar.bz2")
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print('\n File downloaded successfully')
    else:
        print('\n Failed to download file')
        
    print("\n Extracting the source file: ")
    if not os.path.exists(SOURCE_FOLDER):
        run("tar -xjf postgresql-18.1.tar.bz2", cwd=INSTALL_PATH)
    else:
        print("Source folder already exists, skipping extract")
        
def build_postgres():
    print("\n Configuring and Compiling ")
    run(f"./configure --prefix={INSTALL_PATH}" , cwd=SOURCE_FOLDER)
    run("make", cwd=SOURCE_FOLDER)
    run("make install", cwd=SOURCE_FOLDER)
    
def setup_database():
    print("\n Setting up Database")
    data_dir = os.path.join(INSTALL_PATH,f"data")
    bin_dir = os.path.join(INSTALL_PATH,f"bin")
    if not os.path.exists(data_dir):
        run(f"{bin_dir}/initdb -D {data_dir}")
    run(f"{bin_dir}/pg_ctl -D {data_dir} -l logfile start")
    dbname = input("Enter Database Name: ")
    run(f"{bin_dir}/createdb {dbname}")
    
if __name__=="__main__":
    download_source()
    build_postgres()
    setup_database()
    print("\n Postgresql installed successfully")
    
    

