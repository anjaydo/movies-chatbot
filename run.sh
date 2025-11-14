#!/bin/bash
# run.sh
python -W ignore::FutureWarning -m uvicorn app:app --reload --host 127.0.0.1 --port 8000