import json
import os


def readFileData(filename):
    configPath = configPath = os.path.join(
        os.path.expanduser("~"), ".napari", "microscopy_metrics", filename
    )
    if os.path.exists(configPath):
        with open(configPath, "r") as f:
            return json.load(f)
    return {}


def writeFileData(filename, data):
    configDir = os.path.join(
        os.path.expanduser("~"), ".napari", "microscopy_metrics"
    )
    os.makedirs(configDir, exist_ok=True)
    configPath = os.path.join(configDir, filename)
    with open(configPath, "w") as f:
        json.dump(data, f, indent=4)
