import tempfile
from pathlib import Path

import numpy as np
import rasterio as rio

from Fakegeoimages.fakegeoimages import FakeGeoImage


def test_standard_image_4bands():
    with tempfile.TemporaryDirectory() as td:
        test_img, data = FakeGeoImage(6, 4, 4, "uint16", out_dir=Path(td)).create()

        with rio.open(str(test_img)) as src:
            data_from_file = src.read()
            assert np.array_equal(data, data_from_file)
            assert data.dtype == np.uint16
            assert data.shape == (4, 4, 6)
