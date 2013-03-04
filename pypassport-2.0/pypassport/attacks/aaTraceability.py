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
from decimal import *

from signEverything import *

from pypassport.logger import Logger
from pypassport.iso7816 import Iso7816, Iso7816Exception 
from pypassport.reader import PcscReader, ReaderException
from pypassport.doc9303 import mrz, bac
from pypassport.iso9797 import *
from pypassport.hexfunctions import hexToHexRep, binToHexRep

class AATraceabilityException(Exception):
    def __init__(self, *params):
        Exception.__init__(self, *params)

class AATraceability(Logger):
    """
    This class help to identify a passport thanks to the misuses of the active authentication.
    In some case, it is possible to execute an active authentication before the BAC and therefore geting a signature
    In RSA algorythm, the signature can't be higher thant the modulo.
    Therefore, after a couple of test, by keeping the highest signature, we know that we are more and more close  to the modulo
    Since the modulo is unique it is possible to identify (with a little lack of accuracy) a passport
    If the highest signature is higher than the modulo of a passport (avaible in DG15), we know that the passport scanned is NOT the one to which belongs the modulo
    """

    def __init__(self, iso7816):
        Logger.__init__(self, "AA TRACEABILITY")
        self._iso7816 = iso7816
        
        if type(self._iso7816) != type(Iso7816(None)):
            raise AATraceabilityException("The sublayer iso7816 is not available")

        self._iso7816.rstConnection()

        self._bac = None

    def isVulnerable(self):
        """
        This method verify if it is possible to execute a internal authentication BEFORE a BAC
        
        @return: A boolean stating whether the passport is vulnerable or not
        """

        vulnerable = False
        self.log("Reset the connection")
        self._iso7816.rstConnection()
        try:
            rnd = os.urandom(8)
            self.log("Trying to execute an internal authentication")
            if self._iso7816.internalAuthentication(rnd):
                vulnerable = True
        except Iso7816Exception:
            pass
        
        return vulnerable

    def getHighestSign(self, max=100):
        """
        Sign a random number several times (100 by default)
        Keep the highest signature
        
        @param max: The # of loop. The highest the more accurate is suppose to be the output
        @type max: int <1
        
        @return: The highest signature 
        """

        if not self.isVulnerable():
            raise AATraceabilityException("This passport is not vulnerable for a AA traceability")
        
        higher = ""
        i = 0
        self.log("Start the internal authentication loop {0} times".format(max))
        while i<max:
            try:
                rnd = os.urandom(8)
                signature = binToHexRep(self._iso7816.internalAuthentication(rnd))
                if signature > higher:
                    higher = signature
            except Iso7816Exception, msg:
                print msg
            i += 1
        
        return higher
    
    def getModulo(self, mrz_value):
        """
        If an attacker eavesdrop a legitimate communication between a passport and a reader
        it is possible to get the public key used during the AA
        
        @param mrz_value: A MRZ
        @type mrz_value: String value ("PPPPPPPPPPcCCCYYMMDDcSYYMMDDc<<<<<<<<<<<<<<cd")
        
        @return: The modulo from the public key
        """
        
        pub_key = self._getPubKey(mrz_value)
        pub_key_hex = binToHexRep(pub_key)
        self.log("Public key: {0}".format(pub_key_hex))
        modulo = pub_key_hex[58:314]
        self.log("Modulo: {0}".format(modulo))
        return modulo
    
    def _getPubKey(self, mrz_value):
        """
        Calls the method getPubKey() from signEverything
        
        @return: The public key (DG15)
        """
        
        self._bac = bac.BAC(self._iso7816)
        return SignEverything(self._iso7816).getPubKey(self._bac, mrz_value)
    
    def compare(self, modulo, highest, accuracy=6):
        """
        Get the difference between two signature in pourcentage
        
        @param modulo: The first signature (or modulo) to compare
        @type modulo: String of 256 hex (1024bits)
        @param highest: The second signature to compare
        @type highest: String of 256 hex (1024bits)
        @param accuracy: Number of hex to concidare (6 by default)
        @type accuraty: int <1
        
        @return: The difference in pourcentage
        """

        modulo = hexRepToHex(modulo[:accuracy])
        highest = hexRepToHex(highest[:accuracy])
        diff = modulo - highest

        return (1.0*diff/modulo)*100
    
    def mayBelongsTo(self, modulo, highest):
        """
        If the signature is higher than the modulo, this means they both doesn't belong to the same passport
        If it is lower, they both MAY belongs to the same passport
        
        @param modulo: The first signature (or modulo) to compare
        @type modulo: String of 256 hex (1024bits)
        @param highest: The second signature to compare
        @type highest: String of 256 hex (1024bits)
        
        @return: A boolean stating whether the signatures may both belong to the same passport
        """

        modulo = hexRepToHex(modulo)
        highest = hexRepToHex(highest)
        possible = True
        if highest > modulo:
            self.log("The signature is higher than the modulo")
            return not possible
        
        return possible

    def save(self, modulo, path=".", filename="modulo"):
        """
        Save a modulo or a signature for peristant analysis
        If the path doesn't exist, the folders and sub-folders will be create.
        If the file exist, a number will be add automatically.
        
        @param modulo: Modulo (or signature to save)
        @type modulo: String of 256 hex (1024bits)
        @param path: The path where the file has to be create. It can be relative or absolute.
        @type path: A string (e.g. "/home/doe/" or "foo/bar")
        @param filename: The name of the file where the modulo will be saved
        @type filename: A string (e.g. "john-modulo" or "doe.data")
        
        @return: the path and the name of the file where the pair has been saved.
        """

        if not os.path.exists(path): os.makedirs(path)
        if if os.path.exists(os.path.join(path, filename)):
            i=0
            while os.path.exists(os.path.join(path, filename+str(i))):
                i+=1
            fullpath = os.path.join(path, filename+str(i))
        else:
            fullpath = os.path.join(path, filename)
        
        with open(fullpath, 'wb') as file_modulo:
            file_modulo.write(modulo)
        self.log("Modulo/Signature saved at: {0}".format(fullpath))

        return fullpath
    
    def checkFromFile(self, highest, path=os.path.join(".","modulo"), accuracy=None):
        """
        Read a signature stored in a file (by the method self.save()) and compare it with the signature (highest)
        If accuracy is set, the method works like the method compare()
        If accuracy is not set, the method works like mayBelongsTo()
        
        @param highest: Signature
        @type highest: String of 256 hex (1024bits)
        @param path: The path of the file where the modulo has been saved.
        @type path: A string (e.g. "/home/doe/modulo" or "foo/bar/modulo.data")
        @param accuracy: Number of hex to concidare (6 by default)
        @type accuraty: int <1

        @return: pourcentage (if accuracy set) OR boolean
        """

        if not os.path.exists(path): raise MacTraceabilityException("The signature file doesn't exist (path={0})".format(path))
        with open(path, 'rb') as file_modulo:
            signature = file_modulo.read()
                    
        if accuracy:
            sign_dec = hexRepToHex(signature[:accuracy])
            highest_dec = hexRepToHex(highest[:accuracy])
            diff = sign_dec - highest_dec
            return (1.0*diff/sign_dec)*100
        else:
            if signature > highest: return True
            else:   return False
        

