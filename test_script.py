from pathlib import Path

from rasterio.transform import from_origin

from geomockimages.imagecreator import GeoMockImage


if __name__ == "__main__":
    test_image, _ = GeoMockImage(
        600,
        400,
        2,
        "uint16",
        image_type="SAR",
        out_dir=Path("."),
        crs=4326,
        nodata=0,
        nodata_fill=0,
        cog=False,
    ).create(
        seed=22,
        noise_seed=10,
        noise_intensity=2.0,
        transform=from_origin(13.428596, 52.494384, 0.000006, 0.000006),
    )

    print(test_image)
