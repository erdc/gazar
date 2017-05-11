# -*- coding: utf-8 -*-
#  __init__.py
#  gazar
#
#  Created by Alan D Snow, 2017.
#  BSD 3-Clause

"""gazar docstring
This module is a collection of GDAL functions. Documentation can be found
 at `_gazar Documentation HOWTO`_.

.. _gazar Documentation HOWTO:
   https://github.com/snowman2/gazar

"""
from .log import log_to_console, log_to_file
from .meta import version

__version__ = version()
