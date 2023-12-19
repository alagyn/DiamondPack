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

pack()
{
    cd $home
    rm -rf test-dist
    echo "diamondpacking"
    python -m diamondpack --build test-dist \
        --wheels $wheel \
        --scripts examplePackage.myScript \
        --name example \
        --mode $1

}

app()
{
    pack app
    echo ""
    echo "Executing example app"
    $home/test-dist/example/examplePackage.myScript 1 4
}

script()
{
    pack script
    echo ""
    echo "Executing example script"
    $home/test-dist/example/examplePackage.myScript.sh 1 4
}


case $1 in
    app) app ;;
    script) script ;;
    *)
        echo "Usage: run-test.sh [app | script]"
        exit
        ;;
esac

echo ""
echo "Test Done"