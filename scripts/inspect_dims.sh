#!/usr/bin/env bash
set -euo pipefail

echo "=== bd_hgnace_r — indic_sbs ==="
cut -d, -f2 data/raw/eurostat/bd_hgnace_r.tsv | sort -u

echo "=== isoc_r_eb_ain2 — indic_is ==="
cut -d, -f4 data/raw/eurostat/isoc_r_eb_ain2.tsv | sort -u

echo "=== isoc_r_eb_ain2 — size_emp ==="
cut -d, -f3 data/raw/eurostat/isoc_r_eb_ain2.tsv | sort -u