#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game. P3 r24 hold A: the body is read at acquire time.
R=/Users/midir/sm2-n1/_scratch/traversal/r24
echo "== holdA acquired $(date +%T)"
for i in $(seq 1 60); do [ -f $R/READY ] && break; sleep 10; done
[ -f $R/READY ] || { echo "== build not READY after 10 min: exit"; exit 0; }
exec bash $R/holdA_body.sh
