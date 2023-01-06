from __future__ import annotations

import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))  # repository root
# whether a currently running slurm job is in debug mode
DEBUG = "DEBUG" in os.environ or (
    "slurm-submit" not in sys.argv and "SLURM_JOB_ID" not in os.environ
)
# directory to store model checkpoints downloaded from wandb cloud storage
CHECKPOINT_DIR = f"{ROOT}/wandb/checkpoints"
# wandb <entity>/<project name> to record new runs to
WANDB_PATH = "materialsproject/matbench-discovery"

timestamp = f"{datetime.now():%Y-%m-%d@%H-%M-%S}"
today = timestamp.split("@")[0]
