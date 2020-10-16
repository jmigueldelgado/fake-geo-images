"""
Common raster handling methods
"""
from pathlib import Path

from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

from .logging import get_logger

logger = get_logger(__name__)


def to_cog(path_to_image: Path, profile: str = "deflate", **options) -> bool:
    """
    Converts a regular GeoTIFF into a Cloud-optimized GeoTIFF
    Args:
        path_to_image: path to GeoTIFF
        profile: compression profile
        options: additional kwargs (rasterio options"

    Returns:
        True if all went well
    """
    logger.info("Now converting to COG")
    tmp_file_path = Path(str(path_to_image) + ".tmp")
    # pylint: disable=broad-except
    try:
        path_to_image.rename(tmp_file_path)

        # Format creation option (see gdalwarp `-co` option)
        output_profile = cog_profiles.get(profile)
        output_profile.update(dict(BIGTIFF="IF_SAFER"))

        # Dataset Open option (see gdalwarp `-oo` option)
        config = dict(
            GDAL_NUM_THREADS="ALL_CPUS",
            GDAL_TIFF_INTERNAL_MASK=True,
            GDAL_TIFF_OVR_BLOCKSIZE="128",
        )

        cog_translate(
            str(tmp_file_path),
            str(path_to_image),
            output_profile,
            config=config,
            in_memory=False,
            quiet=False,
            **options,
        )
    except Exception:
        # If anything goes wrong we still want to remove the tmp file
        pass
    tmp_file_path.unlink()

    return True
