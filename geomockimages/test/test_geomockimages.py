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
        ).create(
            seed=22,
            noise_seed=10,
            noise_intensity=2.0,
        )

        with rio.open(str(test_img)) as src:
            data_from_file = src.read()
            assert np.array_equal(data, data_from_file)
            assert data.max() < 300
            assert data.dtype == np.uint16
            assert data.shape == (1, 6, 5)


def test_sar_image_2band_nodata():
    """
    Test for a 2-band (dual pol) SAR image such as Sentinei-1 with some nodata
    """
    with tempfile.TemporaryDirectory() as td:
        test_img, data = GeoMockImage(
            5, 3, 2, "uint16", "SAR", out_dir=Path(td)
        ).create(
            seed=22,
            noise_intensity=2.0,
        )

        with rio.open(str(test_img)) as src:
            data_from_file = src.read()
            assert np.array_equal(data, data_from_file)
            assert data.max() < 500
            assert data.dtype == np.uint16
            assert data.shape == (2, 3, 5)


def test_sar_image_1band_pair():
    """
    Test for a pair of SAR 1-band amplitude images that can be used e.g. for change detection
    The created pair has no real changes, only different noise.
    """
    with tempfile.TemporaryDirectory() as td:
        test_img1, data1 = GeoMockImage(
            10, 5, 1, "uint16", "SAR", out_dir=Path(td)
        ).create(seed=4, noise_seed=5, noise_intensity=2.0)

    with tempfile.TemporaryDirectory() as td:
        test_img2, data2 = GeoMockImage(
            10, 5, 1, "uint16", "SAR", out_dir=Path(td)
        ).create(seed=4, noise_seed=3, noise_intensity=2.0)

    # The two images should appear like they were taken at different dates from the same area
    diff = data1.astype(int) - data2.astype(int)
    assert (np.abs(diff)).max() < 150
    assert np.abs(np.sum(diff)) < 1000


def test_sar_image_1band_pair_change():
    """
    Test for a pair of SAR 1-band amplitude images that can be used e.g. for change detection
    The cretaed pair has noch changes.
    """
    with tempfile.TemporaryDirectory() as td:
        _, data1 = GeoMockImage(30, 20, 1, "uint16", "SAR", out_dir=Path(td)).create(
            seed=11, noise_seed=5, noise_intensity=0.01
        )

        test_img, data2 = GeoMockImage(
            30, 20, 1, "uint16", "SAR", out_dir=Path(td)
        ).create(seed=11, noise_seed=5, noise_intensity=0.01, change_pixels=10)

        # Make sure image data was properly written to disk
        with rio.open(str(test_img)) as src:
            data_from_file = src.read()
            assert np.array_equal(data2, data_from_file)

        # 10 pixels values should be changed
        assert np.sum(data1 != data2) == 10


def test_get_change_spot_sizes():
    """
    Test for the get_change_spot_sizes function
    """
    change_pixels_count = 12

    with tempfile.TemporaryDirectory() as td:
        spot_list = GeoMockImage(
            30, 20, 1, "uint16", "SAR", out_dir=Path(td)
        ).get_change_spot_sizes(change_pixels=change_pixels_count)

        assert sum(spot_list) == change_pixels_count


def test_get_change_spot_indices():
    """
    Test for the get_change_spot_indices function
    """
    spot_sizes = [1, 4, 2]

    with tempfile.TemporaryDirectory() as td:
        change_mask = GeoMockImage(
            30, 20, 1, "uint16", "SAR", out_dir=Path(td)
        ).get_change_spot_indices(spot_sizes=spot_sizes)

        assert np.shape(change_mask) == (20, 30)
        assert np.sum(change_mask) == 7


def test_cog():
    with tempfile.TemporaryDirectory() as td:
        test_img, _ = GeoMockImage(
            300, 150, 4, "uint16", out_dir=Path(td), cog=True
        ).create()

        with rio.open(str(test_img)) as src:
            profile = src.profile

            assert profile["compress"] == "deflate"
            assert profile["blockxsize"] == 512
