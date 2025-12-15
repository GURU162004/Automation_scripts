#!/usr/bin/env bash

sudo apt-get update
sudo apt install libpq-dev
sudo apt install build-essential 
sudo apt install libreadline-dev zlib1g-dev libssl-dev libxml2-dev libxslt-dev
sudo apt-get install libcurl4-openssl-dev uuid-dev 
sudo apt-get install git cmake ccache python3 ninja-build nasm yasm gawk lsb-release wget software-properties-common gnupg

#To install clang 19 compiler 
wget https://apt.llvm.org/llvm.sh
chmod +x llvm.sh
sudo ./llvm.sh 19 
#Change the version here based on requirement of the Clickhouse build