import setuptools

import os
import re
import sys
import platform
import subprocess

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from distutils.version import LooseVersion


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the following extensions: " +
                               ", ".join(e.name for e in self.extensions))

        if platform.system() == "Windows":
            cmake_version = LooseVersion(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
            if cmake_version < '3.1.0':
                raise RuntimeError("CMake >= 3.1.0 is required on Windows")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        env = os.environ.copy()
        if "CONDA_BUILD" in env:
            # conda build has this variable available
            py_ver = ".".join(env["PY_VER"].split())
        else:
            # pip build does not
            import sys
            py_ver = sys.version[:3]

        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        # self.debug = True
        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]
        cmake_args = ['-DCMAKE_BUILD_TYPE=' + cfg]
        cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir]
        cmake_args += [f'-DPYBIND11_PYTHON_VERSION={py_ver}']
        cmake_args += ["-GNinja"]
        cmake_args += ["-DCMAKE_CUDA_COMPILER=" + env["CUDACXX"]]


        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),
                                                              self.distribution.get_version())
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.'] + build_args, cwd=self.build_temp)


setup(
    name='spline',
    version='0.10.0.rc.1',
    packages=setuptools.find_packages(),
    ext_modules=[CMakeExtension('spline', '../cpp_cuda_c')],
    cmdclass=dict(build_ext=CMakeBuild),
    include_package_data=True,
    zip_safe=False,
    url='',
    license='GPL3',
    author='Lucas-Raphael Mueller',
    author_email='',
    description=''
)
