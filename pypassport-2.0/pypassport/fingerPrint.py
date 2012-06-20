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

import os
import time
from pypassport import epassport
from pypassport.hexfunctions import *
from pypassport.doc9303.converter import *
from pypassport.apdu import CommandAPDU

from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString

class FingerPrint(object):
    
    def __init__(self, epassport):
        self._doc = epassport
        self._comm = self._doc.getCommunicationLayer()
        self._bac = False
        self._aa = False
        self._aaUnsecure = False
        self._pubKey = False
        self._DSCertificate = False
        self._gen = None
        self._certInfo = None
        
        self._comm.rstConnection()

    def getCertInfo(self):
        return self._certInfo

    def setCertInfo(self, value):
        self._certInfo = value
        
    def analyse(self):
        res = {}
        
        res["activeAuthWithoutBac"] = False
        res["bac"] = "Failed"
        res["DSCertificate"] = False
        res["pubKey"] = False
        res["activeAuth"] = "Failed"
        res["generation"] = 0
        res["certSerialNumber"] = None
        res["certFingerPrint"] = None
        res["ATR"] = None
        res["UID"] = None
        res["DGs"] = "Cannot calculate the DG size"
        res["ReadingTime"] = None
        
        try:
            res["UID"] = binToHexRep(self._comm.getUID())
        except Exception, msg:
            pass
        
        try:
            res["ATR"] = self.getATR()
        except Exception, msg:
            pass
        
        res["activeAuthWithoutBac"] = self.checkInternalAuth()
        self._comm.rstConnection()
            
        #Check if the secure-messaging is set.
        try:        
            sod = self._doc["SecurityData"]
            if self._comm._ciphering:
                res["bac"] = "Done"
        except Exception:
            self._comm.rstConnection()
            
        #Check if there is a certificate 
        try:
            certif = self._doc.getCertificate()
            if certif:
                res["DSCertificate"] = self._doc.getCertificate()
                
                f = open("tmp.cer", "w")
                f.write(certif)
                f.close()
                
                f = os.popen("openssl x509 -in tmp.cer -noout -serial")
                res["certSerialNumber"] = f.read().strip()
                f.close()
                
                f = os.popen("openssl x509 -in tmp.cer -noout -fingerprint")
                res["certFingerPrint"] = f.read().strip()
                f.close()
                
                os.remove("tmp.cer")
        except Exception:
            self._comm.rstConnection() 
                
        
        #Check if there is a pubKey and the AA
        try:
            self._comm.rstConnection()
            if self._doc.getPublicKey():
                res["pubKey"] = self._doc.getPublicKey()
            if self._doc.doActiveAuthentication():
                res["activeAuth"] = "Done"
        except Exception, msg:
            pass

        if not res["bac"]:
            res["generation"] = 1
        
        if res["activeAuth"]:
            if res["activeAuthWithoutBac"]:
                res["generation"] = 3
            else:
                res["generation"] = 2
            
            try:
                self._doc["DG7"]
            except:
                res["generation"] = 4
                    
        try:
            res["DGs"] = self.calculateDGSize()
        except Exception:
            self._comm.rstConnection()
            
        try:
            res["ReadingTime"] = self.calculateReadingTime()
        except Exception, msg:
            pass 
            
        return res
    
    def getATR(self):
        cardtype = AnyCardType()
        cardrequest = CardRequest(timeout=1, cardType=cardtype)
        cardservice = cardrequest.waitforcard()
        
        cardservice.connection.connect()
        return toHexString(cardservice.connection.getATR())
        
    
    def calculateDGSize(self):
        data = {}
        for x in self._doc:
            data[toDG(x)] = len(self._doc[x].file)
            
        return data
            
    def checkInternalAuth(self):
        rnd_ifd = os.urandom(8)
        try:
            self._comm.internalAuthentication(rnd_ifd)
            return True
        except Exception:
            return False
        
    def calculateReadingTime(self):
        for x in self._doc.keys():
            self._doc.__delitem__(x)
            
        start = time.time()
        self._doc.readPassport()
        return time.time() - start
        
