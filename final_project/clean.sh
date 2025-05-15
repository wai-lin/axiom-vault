#!/bin/bash

echo "cleaning..."

find . -maxdepth 1 -name "*.pem" -delete
find . -maxdepth 1 -name "*.gif" -delete
find . -maxdepth 1 -name "*.json" -delete

if [ -d "data" ]; then
  rm -rf data/*
fi
if [ -d "round_reports" ]; then
  rm -rf round_reports
fi


echo "cleanup complete."
