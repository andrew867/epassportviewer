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
from hashlib import *

from pypassport.logger import Logger
from pypassport.iso9797 import *
from pypassport.iso7816 import Iso7816, Iso7816Exception 
from pypassport.reader import PcscReader, ReaderException
from pypassport.doc9303 import mrz, bac, converter, datagroup
from pypassport.doc9303.securemessaging import SecureMessaging
from pypassport.hexfunctions import hexToHexRep, binToHexRep
from pypassport.openssl import OpenSSL, OpenSSLException

class SignEverythingException(Exception):
    def __init__(self, *params):
        Exception.__init__(self, *params)

class SignEverything(Logger):
    """
    This class allows a user to sign any 64bits message.
    The main method is I{sign}
    """
    def __init__(self, iso7816):
        Logger.__init__(self, "SIGN EVERYTHING ATTACK")
        self._iso7816 = iso7816
        
        if type(self._iso7816) != type(Iso7816(None)):
            raise SignEverythingException("The sublayer iso7816 is not available")

        self._iso7816.rstConnection()

        self._bac = bac.BAC(iso7816)
        self._openssl = OpenSSL()
        
    def sign(self, message_to_sign="1122334455667788", mrz_value=None):
        """
        Get the signature of a 64bits message from the reader.
        In order to prevent ICC cloning, the passport implement a Active Authentication (AA) security.
        The passport sign the 64bits message sent by the reader thanks to its Private key store in secured memory.
        This method let the user decide the 64bits and check (if MRZ set) with the public key if the message has been signed properly
        
        @params message_to_sign: 64bits message to sign
        @type message_to_sign: String (16 HEX values)
        
        @return: A set composed of (The signature, Boolean that state if the signature has been checked)
        """
        validated = False
        if mrz_value:
            self.log("Validation required")
            self.log("MRZ: {0}".format(mrz_value))
            public_key = self.getPubKey(self._bac, mrz_value)

        message = message_to_sign
        message_bin = hexRepToBin(message)

        signature = self._iso7816.internalAuthentication(message_bin)
        self.log("Signature: {0}".format(binToHexRep(signature)))
        
        if mrz_value:
            self.log("Check if the signature is correct regarding the public key:")
            data = self._openssl.retrieveSignedData(public_key, signature)
            data_hex = binToHexRep(data)
            header = data_hex[:2]
            self.log("\tHeader: {0}".format(header))
            M1 = data_hex[2:214]
            self.log("\tM1: {0}".format(M1))
            hash_M = data_hex[214:254]
            self.log("\tHash: {0}".format(hash_M))
            trailer = data_hex[254:256]
            self.log("\tTrailer: {0}".format(trailer))
            
            # If using SHA-1
            if header=='6A' and trailer=='BC':
                M = hexRepToBin(M1 + message)
                new_hash = sha1(M).digest()
                hash_M_bin = hexRepToBin(hash_M)
                if new_hash==hash_M_bin:
                    self.log("hash(M|message to sign) == Hash")
                    validated = True
        
        return (binToHexRep(signature), validated)
        
    def getPubKey(self, bac_cp, mrz_value):
        """
        It uses method from pypassport.doc9303.bac in order to authenticate and establish the session keys
        
        @param bac_cp: A BAC for the authentication and establishment of session keys
        @type bac_cp: A pypassport.doc9303.bac.BAC() object
        @param mrz_value: A MRZ
        @type mrz_value: String value ("PPPPPPPPPPcCCCYYMMDDcSYYMMDDc<<<<<<<<<<<<<<cd")
        
        @return: The public key (DG15)
        """
        self.log("Reset conenction")
        self._iso7816.rstConnection()

        self.log("Generate the MRZ object")
        mrz_pass = mrz.MRZ(mrz_value)
        self.log("Check the MRZ")
        mrz_pass.checkMRZ()

        self.log("Authentication and establishment of session keys")
        (KSenc, KSmac, ssc) = bac_cp.authenticationAndEstablishmentOfSessionKeys(mrz_pass)
        self.log("Encryption key: {0}".format(binToHexRep(KSenc)))
        self.log("MAC key: {0}".format(binToHexRep(KSmac)))
        self.log("Send Sequence Counter: {0}".format(binToHexRep(ssc)))
        sm = SecureMessaging(KSenc, KSmac, ssc) 
        self._iso7816.setCiphering(sm)
            
        dgReader = datagroup.DataGroupReaderFactory().create(self._iso7816)
            
        tag = converter.toTAG("DG15")
        dgFile = dgReader.readDG(tag)
        self.log("Get public key")
        dg15 = datagroup.DataGroupFactory().create(dgFile)
        self.log("Public key: {0}".format(binToHexRep(dg15.body)))
        return dg15.body
                    

