#!/bin/bash

URL="https://dpc3.compas.cs.stonybrook.edu/champsim-traces/speccpu/"
OUT_DIR="traces"

mkdir -p "$OUT_DIR"
cd "$OUT_DIR"

# Download all files from the directory
wget -r -np -nH --cut-dirs=2 -A "*.xz" "$URL"

echo "All ChampSim SPEC traces downloaded into $(pwd)"
