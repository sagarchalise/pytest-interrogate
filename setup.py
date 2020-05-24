#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import io
import os

from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        os.path.join(os.path.dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ).read()


setup(
    name="pytest-interrogate",
    version="0.1",
    license="MIT",
    description="Pytest plugin for measuring doscsrting coverage with interrogate.",
    long_description="{0}\n".format(read("README.rst")),
    author="Sagar Chalise",
    py_modules=["pytest_interrogate"],
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "interrogate",
        "pytest",
        "py.test",
        "distributed",
        "parallel",
        "docstring-coverage",
        "docstring",
        "check-docstring",
    ],
    install_requires=["pytest>=4.0", "interrogate>=1.2.0"],
    entry_points={"pytest11": ["pytest_interrogate = pytest_interrogate",],},
)
