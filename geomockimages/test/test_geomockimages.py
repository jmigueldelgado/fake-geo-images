import tempfile
from pathlib import Path

import numpy as np
import rasterio as rio

from geomockimages.imagecreator import GeoMockImage


def test_optical_image_4bands():
    """
    Test for a 4-band (RGBN) optical image
    """
    with tempfile.TemporaryDirectory() as td:
        test_img, data = GeoMockImage(
            6, 4, 4, "uint16", "optical", out_dir=Path(td)
        ).create()

        with rio.open(str(test_img)) as src:
            data_from_file = src.read()
            assert np.array_equal(data, data_from_file)
            assert data.dtype == np.uint16
            assert data.shape == (4, 4, 6)


def test_optical_image_3bands_nodata():
    """
    Test for a 3-band (RGB) optical image with some nodata
    """
    with tempfile.TemporaryDirectory() as td:
        _, data = GeoMockImage(
            6, 4, 4, "uint16", out_dir=Path(td), nodata=1, nodata_fill=3
        ).create()

        assert np.all(data[2, :3, :3] == 1)


def test_optical_image_1band():
    """
    Test for a 1-band (panchromatic) optical image
    """
    with tempfile.TemporaryDirectory() as td:
        test_img, data = GeoMockImage(
            5, 4, 1, "uint16", "optical", out_dir=Path(td)
        ).create(seed=10, noise_seed=6)

    test_ar = np.array([[405, 286], [405, 328], [429, 337]])

    assert np.array_equal(test_ar, data[0][0:3, 1:3])


def test_sar_image_1band():
    """
    Test for a 1-band (single pol) SAR image such as those from ICEYE, Capella or Umbra
    """
    with tempfile.TemporaryDirectory() as td:
        test_img, data = GeoMockImage(
            5, 6, 1, "uint16", "SAR", out_dir=Path(td)
        ).create()

    # The image should have similar characteristics like real image e.g. regarding speckle
    assert False


def test_sar_image_2band_nodata():
    """
    Test for a 2-band (dual pol) SAR image such as Sentinei-1 with some nodata
    """
    with tempfile.TemporaryDirectory() as td:
        test_img, data = GeoMockImage(
            5, 3, 2, "uint16", "SAR", out_dir=Path(td)
        ).create()

    # The image should have similar characteristics like real image e.g. regarding speckle
    assert False


def test_sar_image_1band_pair():
    """
    Test for a pair of SAR 1-band amplitude images that can be used e.g. for change detection
    The cretaed pair has noch changes.
    """
    with tempfile.TemporaryDirectory() as td:
        test_img, data = GeoMockImage(
            5, 3, 1, "uint16", "SAR", out_dir=Path(td)
        ).create(noise_seed=5, noise_intensity=0.5)

    with tempfile.TemporaryDirectory() as td:
        test_img, data = GeoMockImage(
            5, 3, 1, "uint16", "SAR", out_dir=Path(td)
        ).create(noise_seed=3, noise_intensity=0.5)

    # The two images should appear like they were taken at different dates from the same area
    assert False


def test_sar_image_1band_pair_change():
    """
    Test for a pair of SAR 1-band amplitude images that can be used e.g. for change detection
    The cretaed pair has noch changes.
    """
    with tempfile.TemporaryDirectory() as td:
        test_img, data = GeoMockImage(
            15, 8, 1, "uint16", "SAR", out_dir=Path(td)
        ).create(noise_seed=5, noise_intensity=0.5)

    with tempfile.TemporaryDirectory() as td:
        test_img, data = GeoMockImage(
            15, 8, 1, "uint16", "SAR", out_dir=Path(td)
        ).create(noise_seed=3, noise_intensity=0.5, change_pixels=12)

    # The two images should appear like they were taken at different dates from the same area
    # Change could e.g. be a new building

    assert False


def test_cog():
    with tempfile.TemporaryDirectory() as td:
        test_img, _ = GeoMockImage(
            300, 150, 4, "uint16", out_dir=Path(td), cog=True
        ).create()

        with rio.open(str(test_img)) as src:
            profile = src.profile

            assert profile["compress"] == "deflate"
            assert profile["blockxsize"] == 512
