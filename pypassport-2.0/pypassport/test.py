# Copyright 2009 Jean-Francois Houzard, Olivier Roger
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

from pypassport import epassport, reader

def trace(name, msg):
    if name == "EPassport":
        print name + "> " + msg

Sim=True
AA=False
PA=True
HASH_CERTIF=False

MRZ = "EH123456<0BEL8510035M1508075<<<<<<<<<<<<<<02"
READER = "DumpReader"
CSCA_DIR = "testData"
DUMP_DIR = "testData"

r=None

if not Sim:
    r = reader.ReaderManager().waitForCard()
else:
    r = reader.ReaderManager().create(READER)
    r.connect(DUMP_DIR)

ep = epassport.EPassport(r, MRZ)
ep.register(trace)
ep.setCSCADirectory(CSCA_DIR, HASH_CERTIF)

for dg in ep:
    print ep[dg]

if PA:
    try:
        ep.doVerifySODCertificate()
    except Exception, msg:
       print msg
    try:
        p = ep.readDataGroups()
        ep.doVerifyDGIntegrity(p)
    except Exception, msg:
        print msg

if AA:
    ep.doActiveAuthentication()
