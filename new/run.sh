#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Check if libsodium is installed
if ! python -c "import libnacl" &> /dev/null; then
  echo "Installing libsodium system dependencies..."
  if [[ "$(uname)" == "Darwin" ]]; then
    # macOS
    brew install libsodium
  elif [[ "$(uname)" == "Linux" ]]; then
    # Linux
    sudo apt-get update && sudo apt-get install -y libsodium-dev
  fi
fi

# Run the lottery blockchain system with visualization
python main.py --peers 10 --visualize