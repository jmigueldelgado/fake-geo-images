import tempfile
from pathlib import Path

import numpy as np
import rasterio as rio

from fake_geo_images.fakegeoimages import FakeGeoImage


def test_image_4bands():
    with tempfile.TemporaryDirectory() as td:
        test_img, data = FakeGeoImage(6, 4, 4, "uint16", out_dir=Path(td)).create()

        with rio.open(str(test_img)) as src:
            data_from_file = src.read()
            assert np.array_equal(data, data_from_file)
            assert data.dtype == np.uint16
            assert data.shape == (4, 4, 6)


def test_image_3bands_nodata():
    with tempfile.TemporaryDirectory() as td:
        _, data = FakeGeoImage(
            6, 4, 4, "uint16", out_dir=Path(td), nodata=1, nodata_fill=3
        ).create()

        assert np.all(data[2, :3, :3] == 1)


def test_cog():
    with tempfile.TemporaryDirectory() as td:
        test_img, _ = FakeGeoImage(
            300, 150, 4, "uint16", out_dir=Path(td), cog=True
        ).create()

        with rio.open(str(test_img)) as src:
            profile = src.profile

            assert profile["compress"] == "deflate"
            assert profile["blockxsize"] == 128
