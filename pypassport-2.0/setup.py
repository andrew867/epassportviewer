# Copyright 2012 Antonin Beaujeant
#
# This file is part of pypassport.
#
# pypassport is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# pypassport is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with pyPassport.
# If not, see <http://www.gnu.org/licenses/>.

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__),'pypassport', fname)).read()


setup(
    name='pypassport',
    version='2.0',
    description='Python Biometric Passport API',
    author='Jean-Francois Houzard, Olivier Roger and Antonin Beaujeant',
    author_email='jhouzard@gmail.com, folkenda@gmail.com and antonin.beaujeant@uclouvain.be',
    url='http://code.google.com/p/pypassport/downloads/list',
    packages=['pypassport'],
    long_description=read('README'),
    classifiers=[
      "License :: OSI Approved :: GNU Lesser General Public License (LGPL)",
      "Programming Language :: Python",
      "Development Status :: 4 - Beta",
      "Intended Audience :: Developers",
      "Topic :: RFID",
    ],
    keywords='mrtd passport pypassport',
    license='LGPL',
    install_requires=[
        'setuptools', 
        'pyCrypto',
        'pyasn1',
        'pyscard', 
        'PIL'
    ],
    zip_safe = False
      )
