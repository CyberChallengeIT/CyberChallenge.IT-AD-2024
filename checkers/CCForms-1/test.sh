#!/bin/bash

while true; do
    python3 checker.py dev
    if [ $? -ne 101 ]; then
        exit 0
    fi
done