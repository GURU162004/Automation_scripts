#!/usr/bin/env bash

cd ~
git clone --recurse-submodules https://github.com/ClickHouse/ClickHouse.git
cd ClickHouse
git submodule status

export CC=clang-19
export CXX=clang++-19

#Configure build
cmake .. -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=$HOME/clickhouse \
  -DENABLE_TESTS=OFF \
  -DENABLE_BENCHMARKS=OFF \
  -DENABLE_RUST=OFF

ninja -j6
#Change this based on your System Spec and RAM
#If your machine has a RAM of 32 GB, -j6 option is safe. Else, change it to -j4
ninja install

