import subprocess
import sys
import os

DIR_NAME = "installs"
SOURCE_URL = "https://github.com/postgres/postgres.git" 

HOME_DIR = os.path.expanduser("~")
INSTALL_PATH = os.path.join(HOME_DIR, DIR_NAME)
SOURCE_FOLDER = os.path.join(INSTALL_PATH, "postgres")
bin_dir = os.path.join(INSTALL_PATH,"bin")
data_dir = os.path.join(INSTALL_PATH,"data")
vfile = os.path.join(INSTALL_PATH,"version.txt")

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
    run("export LLVM_HOME=$HOME/installs/llvm20")
    run("export PATH=$LLVM_HOME/bin:$PATH")
    run("export LD_LIBRARY_PATH=$LLVM_HOME/lib:$LD_LIBRARY_PATH")
    run(f"CC=clang CXX=clang++ LLVM_CONFIG=$LLVM_HOME/bin/llvm-config LDFLAGS=\"-L$LLVM_HOME/lib -Wl,-rpath,$LLVM_HOME/lib\" CFLAGS=\"-O0 -g3 -fno-omit-frame-pointer -fno-inline\" ./configure --prefix={INSTALL_PATH} --with-pgport=5432 --enable-debug --enable-cassert --enable-depend")
    #Configured to install in a custom folder in home and run at port 5432
    run("make")#Compiles and builds the source
    run("make install")#Installs Postgres from the source.
    with open(vfile,"w") as f:
        f.write(VERSION)

if __name__ == "__main__":
    clone_source()
    run("~/pgsql/bin/initdb -D ~/pgsql/data")#Initialize the data directory.
    print("PostgreSQL Installed Successfully in Debug Mode")