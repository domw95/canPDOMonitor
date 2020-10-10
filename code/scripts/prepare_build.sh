#!/bin/bash

set -e

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)"
. ${THIS_DIR}/versions

# Parse commandline
EXTRA_ARGS=""
DEBUG=""
for var in "$@"; do
  EXTRA_ARGS="${EXTRA_ARGS} -DPEGASUS_CPPLINT_ENABLE=OFF -DPEGASUS_CPPCHECK_ENABLE=OFF"
  EXTRA_ARGS="${EXTRA_ARGS} -DCMAKE_BUILD_TYPE=Debug -DRUN_UNIT_TESTS=true"
  if [ "$var" == "buildonly" ]; then
    EXTRA_ARGS="${EXTRA_ARGS} -DPEGASUS_CPPLINT_ENABLE=OFF -DPEGASUS_CPPCHECK_ENABLE=OFF"
  elif [ "$var" == "test" ]; then
    EXTRA_ARGS="${EXTRA_ARGS} -DRUN_UNIT_TESTS=true"
  elif [ "$var" == "debug" ]; then
    EXTRA_ARGS="${EXTRA_ARGS} -DCMAKE_BUILD_TYPE=Debug -DRUN_UNIT_TESTS=true"
    DEBUG="$var"
  elif [ "$var" == "clangtidy" ]; then
    EXTRA_ARGS="${EXTRA_ARGS} -DCLANG_TIDY_MODE=true -DCMAKE_EXPORT_COMPILE_COMMANDS=ON"
  fi
done

# Set default
#if [ "$DEBUG" == "" ]; then
#  EXTRA_ARGS="${EXTRA_ARGS} -DCMAKE_BUILD_TYPE=Release"
#fi

# Do build
CODE_DIR="${THIS_DIR}/.."
BUILD_DIR=$CODE_DIR/build

echo "Removing existing build from $BUILD_DIR"
rm -Rf $BUILD_DIR
mkdir -p $BUILD_DIR && cd $BUILD_DIR

echo "Preparing build in $BUILD_DIR"
scl enable devtoolset-8 "/opt/hydra/x86_64/cmake-${cmake_ver}/bin/cmake ${EXTRA_ARGS} -DCMAKE_INSTALL_PREFIX=$CODE_DIR/install $CODE_DIR"
