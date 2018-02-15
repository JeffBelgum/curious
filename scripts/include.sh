#!/usr/local/env bash

# Include in all bash scripts to setup and run common functionality.

if [[ ! -f Pipfile ]]; then
  echo "$0 must be run from the project's root directory"
  exit 1
fi

. .env
export PYTHONPATH=.
# manage env file from bash ourselves.
export PIPENV_DONT_LOAD_ENV='true'
