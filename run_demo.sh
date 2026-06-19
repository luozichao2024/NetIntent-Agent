#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[Demo 1] Access control"
python main.py --scenario access

echo "[Demo 2] Latency guarantee with replan"
python main.py --scenario latency

echo "Logs saved to logs/run_logs.json"
