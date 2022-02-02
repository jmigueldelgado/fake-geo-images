# fake-geo-images

A module to programmatically create geotiff images which can be used for unit tests.

<p align="center">
    <img src="./coverage.svg">
</p>

The underlying idea is that in order to write unit tests for geospatial image processsing algorithms, 
it is necessary to have an actual input image file or array. Organising these test images becomes a chore over time,
they should not be stored in git as they are large binary data and when stored outside, there always
is the danger that they are not updated according to changes in the code repo.

**fake-geo-images** provides a solution to the problem by providing simple code that allows to create
geospatial images (so far geotiffs) in a parameterised way. 

## Install package
```bash
pip install fake-geo-images
```

## Run tests
```bash
pytest
```

## Usage

In the following an example unit test for a hypothetical NDVI function.

```python
import numpy as np
import rasterio as rio
from pathlib import Path

from rasterio.transform import from_origin
from my_image_processing import ndvi
from fake_geo_images.fakegeoimages import FakeGeoImage

def test_ndvi():
    """
    A unit test if an NDVI method works in general
    """
    # Create 4-band image simulating RGBN as needed for NDVI
    test_image, _ = FakeGeoImage(
        300,
        150,
        4,
        "uint16",
        out_dir=Path("/tmp"),
        crs=4326,
        nodata=0,
        nodata_fill=3,
        cog=False,
    ).create(seed=42, transform=from_origin(13.428596, 52.494384, 0.000006, 0.000006))

    ndvi_image = ndvi(test_image)

    with rio.open(str(ndvi_image)) as src:
        ndvi_array = src.read()
        # NDVI only has one band of same size as input bands
        assert ndvi_array.shape == (1, 300, 150)
        # NDVI has float values between -1 and 1
        assert ndvi_array.dtype == np.float
        assert ndvi_array.min >= -1
        assert ndvi_array.max <= 1

```


