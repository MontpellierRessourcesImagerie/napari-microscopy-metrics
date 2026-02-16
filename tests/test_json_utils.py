import os
import json
import tempfile
import pytest
from napari_microscopy_metrics.json_utils import *


def test_write_and_read_file_data():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_home = os.path.expanduser("~")
        os.environ["HOME"] = temp_dir
        filename = "test_config.json"
        data = {"first":123, "second":"test"}
        write_file_data(filename,data)
        read_data = read_file_data(filename)
        assert read_data == data
        config_path = os.path.join(os.environ["HOME"],".napari","microscopy_metrics",filename)
        assert os.path.exists(config_path)
        del os.environ["HOME"]
        read_data = read_file_data(filename)
        assert read_data == {}
