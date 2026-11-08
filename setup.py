"""Compatibility shim so `python setup.py sdist` works without `build`.

All metadata lives in pyproject.toml (PEP 621); this file deliberately contains
no duplicated configuration.
"""

from setuptools import setup

setup()
