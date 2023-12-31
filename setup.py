#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "Click>=7.0",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Edward Fretwell",
    author_email="pypi@comfortableshoe.co.uk",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Python modules for interacting with Elecrow GrowCube smart plant watering system",
    entry_points={
        "console_scripts": [
            "pygrowcube=pygrowcube.cli:main",
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="pygrowcube",
    name="pygrowcube",
    packages=find_packages(include=["pygrowcube", "pygrowcube.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/robotedward/pygrowcube",
    version="0.2.0",
    zip_safe=False,
)
