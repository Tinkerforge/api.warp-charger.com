#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
./venv/bin/gunicorn main:app
