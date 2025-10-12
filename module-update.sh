#!/bin/bash

set -e

rm -rf py_modules/submodule

git submodule update --init --recursive

rm -rf py_modules/lib_hid
rm -rf py_modules/serial

# cp -rf submodule/pyhidapi py_modules/submodule/
# cp -rf submodule/pyserial py_modules/submodule/

# cd py_modules && \
# ln -sf submodule/pyhidapi/hid lib_hid && \
# ln -sf submodule/pyserial/serial serial


cp -rf submodule/pyhidapi/hid py_modules/lib_hid
cp -rf submodule/pyserial/serial py_modules/serial
