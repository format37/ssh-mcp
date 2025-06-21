#!/bin/bash
# source ~/miniconda3/etc/profile.d/conda.sh || source ~/anaconda3/etc/profile.d/conda.sh
# conda activate ssh
uvicorn server:app --host 0.0.0.0 --port 7777
