from pathlib import Path
from setuptools import setup, find_packages

parent_dir = Path(__file__).resolve().parent

setup(
    name="fake-geo-images",
    version="0.1.4",
    author="UP42",
    author_email="support@up42.com",
    description="Fake geospatial images for unit tests",
    long_description=parent_dir.joinpath("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/up42/fake-geo-images",
    packages=find_packages(),
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
    ],
    install_requires=parent_dir.joinpath("requirements.txt")
    .read_text(encoding="utf-8")
    .splitlines(),
    python_requires=">=3.6",
)
