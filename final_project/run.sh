#!/bin/bash

for i in {1..10}
do
  python main.py ${i} &
  sleep 2
done

wait
