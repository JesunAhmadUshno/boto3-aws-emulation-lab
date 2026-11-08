"""Record the exact environment of the scored run into
results/versions.json. The pins are part of the result.
"""

import json
import os
import platform
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
import botocore
import moto
import pytest
import requests


def collect():
    return {
        "python": platform.python_version(),
        "boto3": boto3.__version__,
        "botocore": botocore.__version__,
        "moto": moto.__version__,
        "pytest": pytest.__version__,
        "requests": requests.__version__,
        "machine": {
            "hostname": platform.node(),
            "kernel": platform.release(),
            "machine": platform.machine(),
        },
    }


if __name__ == "__main__":
    out = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results",
        "versions.json",
    )
    with open(out, "w") as fh:
        json.dump(collect(), fh, indent=1, sort_keys=True)
    print("wrote", out)
