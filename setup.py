import pathlib
from setuptools import setup, find_packages
from abm import __version__

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="galaxyproject-gxabm",
    version=__version__,
    description="Opinionated Benchmarking Automatation in Galaxy",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/galaxyproject/gxabm",
    author="Keith Suderman",
    author_email="suderman@jhu.edu",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=["pathlib", "bioblend", "pyyaml", "planemo"],
    entry_points={
        "console_scripts": [
            "abm=abm.__main__:entrypoint",
        ]
    },
)