#!/bin/bash

home=$(realpath $(dirname $0))
PY_VER=$(ls $home/venv/lib | grep python)

export PYTHON_HOME=${home}/venv/stdlib
export PYTHON_PATH=${home}/venv/lib/$PY_VER/site-packages
export LD_LIBRARY_PATH=${home}/venv/bin
${home}/venv/bin/python -m @@SCRIPT