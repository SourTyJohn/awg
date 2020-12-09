from setuptools import setup
from Cython.Build import cythonize

setup(
    name='AWG',
    ext_modules=cythonize("core/physic/Physics.pyx"),
    zip_safe=False,
)
