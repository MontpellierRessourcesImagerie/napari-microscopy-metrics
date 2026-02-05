import json
import os


def read_file_data(filename):
    config_path = config_path = os.path.join(os.path.expanduser("~"), ".napari", "microscopy_metrics", filename)
    if os.path.exists(config_path):
        with open(config_path,"r") as f :
            return json.load(f)
    return {}

def write_file_data(filename,data):
    config_dir = os.path.join(os.path.expanduser("~"), ".napari","microscopy_metrics")
    os.makedirs(config_dir,exist_ok=True)
    config_path = os.path.join(config_dir, filename)
    with open(config_path,"w") as f : 
        json.dump(data, f, indent=4)
