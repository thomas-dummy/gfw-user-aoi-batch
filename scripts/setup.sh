#!/usr/bin/env bash

pip install -r requirements.txt
pip install -e .

detect-secrets scan > .secrets.baseline
pre-commit install
