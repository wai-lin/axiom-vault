#!/bin/bash

for i in {1}
do
  python main.py ${i} &
  sleep 1
done

wait
