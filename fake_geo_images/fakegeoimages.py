"""
Utility class to generate synthetic images, especially useful for testing purposes.
"""

import uuid
from pathlib import Path
from typing import Union, List

import rasterio
from rasterio import crs as rio_crs
from rasterio.transform import from_origin
import skimage.draw
from scipy import signal
import numpy as np

from .logging import get_logger
from .raster import to_cog

logger = get_logger(__name__)

# Define standard land cover classes and representative stats wrt radiance for a 4-band product
LC_CLASSES = {
    "water": {"avg": [170, 300, 450, 150], "std": [10, 10, 10, 10]},
    "bare_ground": {"avg": [600, 600, 600, 900], "std": [100, 100, 100, 100]},
    "built_up": {"avg": [800, 800, 800, 1000], "std": [150, 150, 150, 150]},
    "forest": {"avg": [250, 450, 450, 1300], "std": [30, 30, 30, 30]},
    "non-forest_vegetation": {
        "avg": [300, 500, 500, 1100],
        "std": [100, 100, 100, 100],
    },
}


class FakeGeoImage:
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-instance-attributes
    """
    Create synthetic GeoTIFF test image. An image created this way cannot recreate all characteristics of a
    real geospatial image, but if cleverly created can avoid having to use golden files for a
    long list of cases.
    """

    def __init__(
        self,
        xsize: int,
        ysize: int,
        num_bands: int,
        data_type: str,
        out_dir: Path = Path("."),
        crs: int = 3857,
        nodata: Union[int, float] = 0,
        nodata_fill: int = 0,
        cog: bool = False,
    ):
        """
        Args:
            xsize: Number of pixels in x-direction.
            ysize: Number of pixels in y-direction.
            num_bands: Number of image bands.
            data_type: Rasterio datatype as string.
            out_dir: Path where the image should be created. Defaults to a random id if not provided..
            crs: EPSG identifier of used coordinate reference system (default 3837).
            nodata: Value representing nodata within each raster band, default is 0. If set to -1 no nodata value set.
            nodata_fill: number of no data pixels to set in top left image (in x and y).
            cog: Output is a cloud-optimized geotiff. Only makes sense for larger images where block size matters.

        Example:
            ```python
            input_img, an_array = FakeGeoImage(
                10, 10, 4, "uint16", input_dir, nodata_fill=3
            ).create(seed=45)
            ```
        """

        self.xsize = xsize
        self.ysize = ysize
        self.num_bands = num_bands
        self.data_type = data_type
        self.out_dir = out_dir
        self.crs = crs
        self.nodata_fill = nodata_fill
        if nodata == -1:
            self.nodata = None
        else:
            self.nodata = nodata
        self.cog = cog

    def add_img_pattern(self, seed: Union[int, None]) -> List[np.ndarray]:
        """
        Simulate a five classes optical image.

        Args:
            seed: A random seed number. Ensures reproducibility.

        Returns:
            List of numpy array bands representing simulated image.
        """
        if seed is not None:
            np.random.seed(seed)

        image, _ = skimage.draw.random_shapes(
            (self.ysize, self.xsize),
            max_shapes=50,
            min_shapes=25,
            multichannel=False,
            allow_overlap=True,
            random_seed=seed,
        )
        # Assign shape values to output classes
        image[image < 55] = 1
        image[(image >= 55) & (image < 105)] = 2
        image[(image >= 105) & (image < 155)] = 3
        image[(image >= 155) & (image < 205)] = 4
        image[(image >= 205) & (image <= 255)] = 5

        # Create bands having relevant values for all output classes
        bands = []
        band_idx = 0
        while band_idx < self.num_bands:
            data_ar = np.zeros_like(image, dtype=self.data_type)

            for class_idx, lc_class in enumerate(LC_CLASSES.values(), 1):
                # Add Gaussian noise
                try:
                    mask_ar = np.random.normal(
                        lc_class["avg"][band_idx],
                        lc_class["std"][band_idx],
                        image.shape,
                    )
                except IndexError:
                    mask_ar = np.random.normal(
                        lc_class["avg"][-1], lc_class["std"][-1], image.shape
                    )
                data_ar[image == class_idx] = mask_ar[
                    image == class_idx
                ]  # pylint: disable=unsubscriptable-object
            # Apply median filter to simulate spatial autocorrelation
            data_ar = (signal.medfilt(data_ar)).astype(self.data_type)
            data_ar = np.clip(data_ar, 1, None)
            bands.append(data_ar)
            band_idx += 1

        return bands

    def create(
        self,
        seed: Union[int, None] = None,
        transform: rasterio.Affine = from_origin(1470996, 6914001, 2.0, 2.0),
        file_name: Union[str, None] = None,
        band_desc: Union[list, None] = None,
    ) -> tuple:
        """
        Creates a synthethic image file with a given seed. Returns a tuple with
        (path to file, array).
        Transform is set by default to `from_origin(1470996, 6914001, 2.0, 2.0)`. Pass
        another Affine transform if needed.

        Arguments:
            seed: A random seed number. Ensures reproducibility.
            transform: An Affine transform for the image to be generated.
            file_name: A name for the created file.
            band_desc: List with descriptions (strings) for each band.

        Returns:
            Path to the output image, numpy array of image values.
        """
        band_list = self.add_img_pattern(seed)

        if not file_name:
            filepath = self.out_dir.joinpath(str(uuid.uuid4()) + ".tif")
        else:
            filepath = self.out_dir.joinpath(file_name + ".tif")

        # Even though we don't want a nodata value to be set, we still need a value that represents it for image
        # creation purposes
        if self.nodata is None:
            nodata_val = 0
        else:
            nodata_val = self.nodata  # type: ignore
        with rasterio.open(
            filepath,
            "w",
            driver="GTiff",
            height=self.ysize,
            width=self.xsize,
            count=self.num_bands,
            dtype=str(band_list[0].dtype),
            crs=rio_crs.CRS.from_epsg(self.crs),
            transform=transform,
            nodata=self.nodata,
        ) as out_img:
            for band_id, layer in enumerate(band_list):
                layer[0 : self.nodata_fill, 0 : self.nodata_fill] = nodata_val
                out_img.write_band(band_id + 1, layer)
                if band_desc is not None:
                    try:
                        out_img.set_band_description(band_id + 1, band_desc[band_id])
                    except IndexError:
                        logger.debug(
                            "Number of band descriptions does not match number of bands"
                        )

        if self.cog:
            to_cog(Path(filepath))

        return filepath, np.array(band_list)
