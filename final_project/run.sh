#!/bin/bash

for i in {1..20}
do
  python main.py &
  sleep 0.2
done

wait
