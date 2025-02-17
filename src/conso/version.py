# -*- coding: utf-8 -*-

"""Version information for the CONSO python package."""

__all__ = [
    'VERSION',
    'get_version',
]

VERSION = '1.0.1-dev'


def get_version() -> str:
    """Get the software version of CONSO."""
    return VERSION
