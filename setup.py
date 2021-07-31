from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext


if __name__ == "__main__":  # setup.py build_ext -i clean
    ext_modules = [Extension('linear', sources=['core/math/linear.pyx'], language='c',)]

    setup(
        name='linear',
        cmdclass={'build_ext': build_ext},
        ext_modules=ext_modules
    )
