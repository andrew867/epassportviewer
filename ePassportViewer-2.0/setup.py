# Copyright 2009 Jean-Francois Houzard, Olivier Roger
#
# This file is part of epassportviewer.
#
# epassportviewer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# epassportviewer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with epassportviewer.
# If not, see <http://www.gnu.org/licenses/>.

import sys
from setuptools import setup, find_packages


NAME = "ePassport Viewer"
VERSION = "1.0"
MAIN = "epassportviewer/ePassportViewer.py"

BASE = 'C:/Python25/Lib/site-packages/cx_Freeze/bases/Win32GUI.exe'

if sys.platform == 'darwin':
	# http://mail.python.org/pipermail/pythonmac-sig/2007-July/019092.html
	PLIST = {\
	             'PyResourcePackages': [
	                 'lib/python2.5',
	                 'lib/python2.5/lib-dynload',
	                 'lib/python2.5/site-packages.zip',
	             ],
	             'CFBundleName'               : NAME,
	             'CFBundleIconFile'           : "app.icns",
	             'CFBundleShortVersionString' : VERSION,
	             'CFBundleGetInfoString'      : NAME + " " + VERSION,
	             'CFBundleExecutable'         : NAME,
	             'CFBundleIdentifier'         : "be.uclouvain.epassportviewer",
	         }
	
	OPTIONS = {
	            'argv_emulation': True,
	            'plist': PLIST,
	}

	extra_options = dict(
		setup_requires = ['py2app'],
		app = [MAIN],
		iconfile = 'app.icns',
		data_files = ['./epassportviewer', './Geojasper/geojasper', './app.icns'],
		options = {'py2app': OPTIONS},
		loader_files = (".",['setuptools', 'pypassport', 'reportlab', 'PIL', 'smartcard', 'pycrypto', 'pyasn1']),	
    )
    
elif sys.platform == 'win32':
    from cx_Freeze import Executable, setup
    extra_options = dict(
	    entry_points = {
	        'gui_scripts': [
	            'epassportviewer = epassportviewer.ePassportViewer:run',
	        ]
	    },
	    executables = [Executable(MAIN,
	                              base=BASE,
	                              compress=True,
	                              icon = "app.ico",
	                              )],
	    install_requires = ['setuptools', 'pypassport', 'reportlab', 'PIL'],
    )
    
else:
	print "Unhandled platform"
	sys.exit(-1)

setup(
    name=NAME,
    version = VERSION,
    description='Python Biometric Passport Viewer',
    author='Jean-Francois Houzard & Olivier Roger',
    author_email='jhouzard@gmail.com & olivier.roger@gmail.com',
    url='http://code.google.com/p/epassportviewer/',

    packages = find_packages(),

    # metadata for upload to PyPI
    license = "GPL",
    keywords = "mrtd passport pypassport",
    
    **extra_options
)
