# encoding: utf-8

from setuptools import setup, find_packages


setup(
    name='pylxd-light',
    version='0.0.0',
    author='Hiroaki Nakamura, James Pic',
    author_email='jamespic@gmail.com',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    include_package_data=True,
    url='https://github.com/novafloss/pylxd-light',
    description='Experimental alternative to pylxd',
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
    install_requires=[
        'requests',
        'requests_unixsocket',
    ],
)
