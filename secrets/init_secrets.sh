#!/bin/bash

# copy all ".default.txt" files into plain ".txt" files
for f in *.default.txt; do
    if [ -f "$f" ] && [ ! -f "${f%.default.txt}.txt" ]; then
        cp "$f" "${f%.default.txt}.txt"
    fi
done