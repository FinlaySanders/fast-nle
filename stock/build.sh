#!/bin/bash
# Run from the PufferLib root after ./build.sh nethack. Builds two libraries:
#   stock/build/libnethack.so  the stock backend as a drop-in for the fork library: LD_LIBRARY_PATH=vendor/fast-nle/stock/build ./puffer eval ... (see ./puffer_stock)
#   stock/libnhagent.so        the env, its CPU forward pass and the reconstruction, for the gym driver nhc_agent.py
set -e; cd "$(dirname "$0")/../../.."
NLE=vendor/fast-nle; CC=${CC:-clang}; mkdir -p $NLE/stock/build
$CC -O2 -shared -fPIC -I$NLE/stock -I$NLE/include -I$NLE/build/_deps/deboost_context-src/include $NLE/stock/nh_stock_backend.c -o $NLE/stock/build/libnethack.so -ldl
INC="-I. -Isrc -Iocean/nethack -I$NLE/stock -Ivendor -I$NLE/include -I$NLE/build/_deps/deboost_context-src/include -Iraylib-5.5_linux_amd64/include"
$CC -O2 -fPIC -c $INC -DPLATFORM_DESKTOP -DPUFFER_NETHACK $NLE/stock/nh_gym_backend.c -o $NLE/stock/build/nh_gym_backend.o
$CC -O2 -fPIC -c $INC -fopenmp -DPLATFORM_DESKTOP -DPUFFER_NETHACK $NLE/stock/nh_gym_runner.c -o $NLE/stock/build/nh_gym_runner.o
$CC -shared -fopenmp $NLE/stock/build/nh_gym_backend.o $NLE/stock/build/nh_gym_runner.o -o $NLE/stock/libnhagent.so -lm -lpthread
echo "Built: $NLE/stock/build/libnethack.so (stock backend), $NLE/stock/libnhagent.so (gym driver)"
