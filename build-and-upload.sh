#!/bin/bash

cd $(realpath `dirname $0`)

rm -rf dist/*
./venv/bin/python -m build
./venv/bin/python -m twine upload -r diamondpack dist/*
