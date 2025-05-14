#!/bin/bash

for i in {1..20}
do
  python main.py ${i} &
  sleep 2
done

wait
