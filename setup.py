from setuptools import setup
from Cython.Build import cythonize

import numpy
import pymunk
import beartype


MATH_LINEAR_BUILD = [numpy.get_include(), ]

setup(
    ext_modules=cythonize("core/accelerated/linear.pyx")
)
