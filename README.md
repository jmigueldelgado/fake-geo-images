# fake-geo-images
A module to programmatically create geotiff images which can be used for unit tests.

The underlying idea is that in order to write unit tests for geospatial image processsing algorithms, 
it is necessary to have an actual input image. Organising these test images becomes a chore over time,
they should not be stored in git as they are large binary data and when stored outside, there always
is the danger that they are not updated according to changes in the code repo.

**fake-geo-images** provides a solution to the problem by providing simple code that allows to create
geospatial images (so far geotiffs) in a parameterised way. 

## Install package
```bash
pip install image-similarity-measures
```

## Usage

In the following an example unit test for a hypothetical NDVI function.

```python
import numpy as np
import rasterio as rio

from my_image_processing import ndvi
from fake_geo_images import fakegeoimages

def test_ndvi():
    """
    A unit test if an NDVI method works in general
    """
    # Create 4-band image simulating RGBN as needed for NDVI
    test_image, _ = fakegeoimages.FakeGeoImage(
            300, 150, 4, "uint16"
        )

    ndvi_image = ndvi(test_image)

    with rio.open(str(test_image)) as src:
        ndvi_array = src.read()
        # NDVI only has one band of same size as input bands
        assert ndvi_array.shape == (1, 300, 150)
        # NDVI has float values between -1 and 1
        assert ndvi_array.dtype == np.float
        assert ndvi_array.min >= -1
        assert ndvi_array.max <= 1

```


