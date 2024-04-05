#!/bin/bash

home=$(realpath $(dirname $0))

export PYTHONHOME=${home}/venv/
export PYTHONPATH=${home}/venv/lib/@@PYTHON@@/site-packages
export LD_LIBRARY_PATH=${home}/venv/bin
"${home}/venv/bin/python" @@COMMAND@@ $@