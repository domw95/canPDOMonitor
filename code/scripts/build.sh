#!/bin/bash

# Copyright (c) 2019 BAE Systems Applied Intelligence. All rights reserved.

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)"
. ${THIS_DIR}/versions

CODE_DIR="${THIS_DIR}/.."
BUILD_DIR=$CODE_DIR/build

if [ ! -d $BUILD_DIR ]; then 
  echo "Directory /path/to/dir DOES NOT exists."
  mkdir $BUILD_DIR
fi

if $CODE_DIR/scripts/prepare_build.sh buildonly test; then
  cd $BUILD_DIR
  parallel=$((`cat /proc/cpuinfo | grep processor | tail -n1 | awk '{ print $3 }'`+2))
  if scl enable devtoolset-${devtoolset_ver} "make -j${parallel} -k install"; then
    exit 0
  fi
fi

exit 1
