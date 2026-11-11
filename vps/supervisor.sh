#!/usr/bin/env bash
# Superviseur du moissonnage : relance harvest.py apres un arret
# anormal (reseau, XML mal forme) ; s'arrete quand HARVEST.done existe.
set -u
cd "$(dirname "$0")"
mkdir -p logs spool
while true; do
    if [ -f HARVEST.done ]; then
        echo "$(date -Is) moissonnage termine (HARVEST.done)"
        break
    fi
    python3 harvest.py >> logs/harvest.log 2>&1
    rc=$?
    if [ -f HARVEST.done ]; then
        echo "$(date -Is) moissonnage termine (rc=$rc)"
        break
    fi
    echo "$(date -Is) harvest.py sorti (rc=$rc), relance dans 60 s" >> logs/harvest.log
    sleep 60
done
