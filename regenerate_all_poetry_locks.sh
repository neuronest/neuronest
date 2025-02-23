#!/bin/bash

PARENT_DIR="$(pwd)"

for DIR in "$PARENT_DIR"/*/; do
  if [ -d "$DIR" ] && [ -f "$DIR/pyproject.toml" ]; then
    echo "Processing directory: $DIR"
    
    cd $DIR && touch poetry.lock && rm poetry.lock && poetry lock
    
  fi
done
