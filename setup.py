import os
from pathlib import Path
import setuptools

PARENT_DIR = Path(__file__).resolve().parent


def set_directory():
    # CD to this directory, to simplify package finding
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)


set_directory()

with open("docs/index.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="fake-geo-images",
    version=PARENT_DIR.joinpath("fake-geo-images/_version.txt").read_text(encoding="utf-8"),
    author="UP42",
    author_email="support@up42.com",
    description="Fake geospatial images for unit tests",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://www.up42.com",
    packages=setuptools.find_packages(exclude=("tests")),
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
    ],
    install_requires=[
        "numpy",
        "rasterio",
        "scipy",
        "scikit-image",
        "rio-cogeo"
    ],
    python_requires=">=3.6, <3.9",
)
