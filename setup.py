"""
Setup file for the PictureBox package.

The only required fields for setup are name, version, and packages. Other fields to consider (from looking at other
projects): keywords, include_package_data, requires, tests_require, package_data
"""
from setuptools import setup

#with open('requirements.txt') as f:
#    requirements = f.read().splitlines()

setup(
    name='picturebox',
    version='0.1',
    author='kwan3217',
    author_email='kwan3217@gmail.com',
    description='Science data processing pipeline for the EMM-EXI instrument',
    python_requires='>=3.8, <4',
    url='https://github.com/kwan3217/picturebox.git',
    classifiers=[
        "Natural Language :: English",
        "Topic :: Scientific/Engineering",
        "Programming Language :: Python :: 3.8"
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
    ],
    packages=['picturebox'],
    install_requires=["matplotlib","numpy","kwanmath"]
)
