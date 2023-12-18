#!/bin/bash
set -e

home=$(realpath $(dirname $0))

cd $home

source $home/venv/bin/activate

wheel=test/dist/example-1.0.0-py3-none-any.whl

if ! [ -f $wheel ]
then
    echo "Building test wheel"
    cd test
    python -m build --wheel
fi

cd $home
rm -rf test-dist
echo "diamondpacking"
python -m diamondpack --build test-dist --wheels $wheel --scripts examplePackage.myScript
echo "Done"