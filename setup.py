import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="fake-geo-images",
    version="0.1.0",
    author="UP42",
    author_email="support@up42.com",
    description="Fake geospatial images for unit tests",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/up42/fake-geo-images",
    packages=setuptools.find_packages(),
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
    ],
    install_requires=["numpy", "rasterio", "scipy", "scikit-image", "rio-cogeo"],
    python_requires=">=3.6, <3.9",
)
