"""
Utility class to generate synthetic images, especially useful for testing purposes.
"""

import random
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
LC_CLASSES_OPTICAL = {
    "water": {"avg": [170, 300, 450, 150], "std": [10, 10, 10, 10]},
    "bare_ground": {"avg": [600, 600, 600, 900], "std": [100, 100, 100, 100]},
    "built_up": {"avg": [800, 800, 800, 1000], "std": [150, 150, 150, 150]},
    "forest": {"avg": [250, 450, 450, 1300], "std": [30, 30, 30, 30]},
    "non-forest_vegetation": {
        "avg": [300, 500, 500, 1100],
        "std": [100, 100, 100, 100],
    },
}

# Define standard land cover classes and representative stats wrt C-band HH and HV amplitude as found in Sentinel-1
LC_CLASSES_SAR = {
    "water": {"avg": [30, 50], "std": [10, 10]},
    "bare_ground": {"avg": [60, 140], "std": [30, 50]},
    "built_up": {"avg": [140, 300], "std": [50, 150]},
    "forest": {"avg": [90, 180], "std": [30, 40]},
    "non-forest_vegetation": {
        "avg": [70, 140],
        "std": [30, 80],
    },
}


class GeoMockImage:
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
        image_type: str = "optical",
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
        self.image_type = image_type
        self.out_dir = out_dir
        self.crs = crs
        self.nodata_fill = nodata_fill
        if nodata == -1:
            self.nodata = None
        else:
            self.nodata = nodata
        self.cog = cog

    def create(
        self,
        seed: Union[int, None] = None,
        noise_seed: Union[int, None] = None,
        noise_intensity: float = 1.0,
        change_pixels: int = 0,
        transform: rasterio.Affine = from_origin(1470996, 6914001, 2.0, 2.0),
        file_name: Union[str, None] = None,
        band_desc: Union[list, None] = None,
    ) -> tuple:
        """
        Creates a synthetic image file with a given seed. Returns a tuple with
        (path to file, array).
        Transform is set by default to `from_origin(1470996, 6914001, 2.0, 2.0)`. Pass
        another Affine transform if needed.

        Arguments:
            image_type: either 'optical' or 'SAR', optical by default
            seed: A random seed number. Ensures reproducibility.
            noise_seed: used when multiple images with the same seed are created that have slight differences e.g. when simulating a time series
            transform: An Affine transform for the image to be generated.
            file_name: A name for the created file.
            band_desc: List with descriptions (strings) for each band.

        Returns:
            Path to the output image, numpy array of image values.
        """
        band_list = self.add_img_pattern(
            seed, noise_seed, noise_intensity, change_pixels
        )

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

    def add_img_pattern(
        self,
        seed: Union[int, None],
        noise_seed: Union[int, None],
        noise_intensity: float = 1.0,
        change_pixels: int = 0,
    ) -> List[np.ndarray]:
        """
        Simulate a five classes optical or SAR image.
        Creates reasonable results for optical images with 3 or 4 bands and SAR images with 1 or 2 bands polorisations.
        The method does also work with any number of bands, but the results will be less realistic.

        Args:
            seed: A random seed number. Ensures reproducibility.
            noise_seed: A random seed number for noise
            noise_intensity: multiplier for noise
            change_pixels: number of pixels that are changed from the original value. Usable for change detection purposes

        Returns:
            List of numpy array bands representing simulated image.
        """
        image, _ = skimage.draw.random_shapes(
            (self.ysize, self.xsize),
            max_shapes=50,
            min_shapes=25,
            channel_axis=None,
            allow_overlap=True,
            rng=seed,
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

            if self.image_type == "optical":
                lc_values = enumerate(LC_CLASSES_OPTICAL.values(), 1)
            elif self.image_type == "SAR":
                lc_values = enumerate(LC_CLASSES_SAR.values(), 1)
            else:
                raise Exception("Only optical and SAR images are supported")

            for class_idx, lc_class in lc_values:
                # Add Gaussian noise
                try:
                    mask_ar = np.random.default_rng(seed=noise_seed).normal(
                        lc_class["avg"][band_idx],
                        lc_class["std"][band_idx] * noise_intensity,
                        image.shape,
                    )
                except IndexError:
                    mask_ar = np.random.default_rng(seed=noise_seed).normal(
                        lc_class["avg"][-1],
                        lc_class["std"][-1] * noise_intensity,
                        image.shape,
                    )
                data_ar[image == class_idx] = mask_ar[image == class_idx]
            # Apply median filter to simulate spatial autocorrelation
            data_ar = (signal.medfilt(data_ar)).astype(self.data_type)
            data_ar = np.clip(data_ar, 1, None)
            bands.append(data_ar)
            band_idx += 1

            if change_pixels > 0:
                bands = self.add_change_pixels(
                    bands=bands,
                    seed=seed,
                    noise_intensity=noise_intensity,
                    change_pixels=change_pixels,
                )

        return bands

    def add_change_pixels(
        self,
        bands,
        seed: Union[int, None],
        noise_intensity: float = 1.0,
        change_pixels: int = 0,
    ) -> List[np.ndarray]:
        """
        Args:
            seed: A random seed number. Ensures reproducibility.
            noise_seed: A random seed number for noise
            noise_intensity: multiplier for noise
            change_pixels: number of pixels that are changed from the original value. Usable for change detection purposes
        Returns:
            List of numpy array bands representing simulated image.

        """
        logger.info("Now adding change pixels")
        change_spot_sizes = self.get_change_spot_sizes(change_pixels)
        change_spot_indices = self.get_change_spot_indices(change_spot_sizes)
        bands = self.apply_change(bands, change_spot_indices)

        return bands

    def get_change_spot_sizes(self, change_pixels: int) -> List[int]:
        """
        Args:
            change_pixels: number of pixels that are changed from the original value. Usable for change detection purposes
        Returns:
            List of change spot sizes.
        """
        # change spots can consist of 4..change_pixels pixels.
        rng = np.random.default_rng()
        pixels_left = change_pixels
        change_patches = []
        while pixels_left > 0:
            patch_size = rng.integers(1, 11)
            if pixels_left - patch_size < 0:
                patch_size = pixels_left
                pixels_left = 0
            change_patches.append(patch_size)
            pixels_left -= patch_size

        return change_patches

    def get_change_spot_indices(self, spot_sizes):
        """
        Given the sizes of the change spots, this method identifies their spatial location within the image
        Args:
            spot_sizes: List of sizes of the change spots
        Returns:
            A boolean mask showing the location of the change pixels.
        """
        spot_sizes_orig = spot_sizes
        directions = ["u", "d", "r", "l"]
        change_pixels = []
        remaining_pxls = sum(spot_sizes)

        while remaining_pxls > 0:
            # Sample the 2D image space to get the centers of the change spots
            yx = np.random.rand(len(spot_sizes), 2)

            yx[:, 0] = yx[:, 0] * (self.ysize - 1)
            yx[:, 1] = yx[:, 1] * (self.xsize - 1)
            yx = np.rint(yx).astype(int)

            for i in range(len(spot_sizes)):
                pxls = [(int(yx[i][0]), int(yx[i][1]))]  # This is the starting pixel

                for next_step in range(spot_sizes[i]):
                    nextmove = random.sample(directions, 1)[0]
                    match nextmove:
                        case "u":
                            logger.debug("u")
                            newpix_np = pxls[-1] + np.array([1, 0])
                        case "d":
                            logger.debug("d")
                            newpix_np = pxls[-1] + np.array([-1, 0])
                        case "l":
                            logger.debug("l")
                            newpix_np = pxls[-1] + np.array([0, -1])
                        case "r":
                            logger.debug("r")
                            newpix_np = pxls[-1] + np.array([0, 1])
                    newpix = (int(newpix_np[0]), int(newpix_np[1]))

                    if (
                        newpix[0] >= self.ysize
                        or newpix[1] >= self.xsize
                        or newpix[0] < 0
                        or newpix[0] < 0
                    ):
                        continue  # avoiding duplicates
                    pxls.append(newpix)
                    change_pixels.append(newpix)
                logger.info(pxls)

            logger.debug(change_pixels)
            change_pixels_set = set(change_pixels)  # This removes duplicates

            remaining_pxls = sum(spot_sizes_orig) - len(change_pixels_set)
            spot_sizes = [remaining_pxls]

        idxs = (tuple(i[0] for i in change_pixels), tuple(i[1] for i in change_pixels))

        change_mask = np.zeros((self.ysize, self.xsize), dtype=bool)
        change_mask[idxs] = True

        return change_mask

    def apply_change(self, bands, spot_indices, change_factor=1.3):
        """
        Args:
            bands: List of numpy arrays representing simulated image.
            spot_indices: A boolean mask showing the location of the change pixels.
        Returns:
            List of numpy array bands representing simulated image.
        """
        for i in range(self.num_bands):
            bands[i][spot_indices] = bands[i][spot_indices] * change_factor

        return bands
