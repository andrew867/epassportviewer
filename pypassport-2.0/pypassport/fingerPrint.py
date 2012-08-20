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
from pypassport.iso7816 import Iso7816Exception
from pypassport.doc9303 import passiveauthentication
from pypassport import epassport, iso7816
from pypassport.hexfunctions import *
from pypassport.doc9303.converter import *
from pypassport.apdu import CommandAPDU
from pypassport.attacks import macTraceability

from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString

class FingerPrint(object):
    
    def __init__(self, epassport, callback=None):
        self._doc = epassport
        self.curMRZ = None
        self._comm = self._doc.getCommunicationLayer()
        self._pa = passiveauthentication.PassiveAuthentication(epassport)
        self._certInfo = None
        self.callback = callback
        
        self._comm.rstConnection()

    def getCertInfo(self):
        return self._certInfo

    def setCertInfo(self, value):
        self._certInfo = value
        
    def analyse(self):
        res = {}
        
        res["activeAuthWithoutBac"] = False
        res["macTraceability"] = False
        res["blockAfterFail"] = False
        res["delaySecurity"] = False
        res["selectNull"] = "N/A"
        res["bac"] = "Failed"
        res["DSCertificate"] = "Document Signer Certificate: N/A"
        res["pubKey"] = "Private key: N/A"
        res["activeAuth"] = "Failed"
        res["generation"] = 0
        res["certSerialNumber"] = "N/A"
        res["certFingerPrint"] = "N/A"
        res["ATR"] = "N/A"
        res["UID"] = "N/A"
        res["DGs"] = "Cannot calculate the DG size"
        res["ReadingTime"] = "N/A"
        res["SOD"] = "N/A"
        res["Integrity"] = "N/A"
        res["Hashes"] = "N/A"
        res["failedToRead"] = list()
        res["EP"] = dict()
        
        try:
            res["UID"] = binToHexRep(self._comm.getUID())
        except Exception, msg:
            pass
        
        try:
            res["ATR"] = self.getATR()
        except Exception, msg:
            pass
        
        res["blockAfterFail"] = self.blockAfterFail()
        
        res["activeAuthWithoutBac"] = self.checkInternalAuth()
        
        res["macTraceability"] = self.checkMACTraceability()
        
        res["selectNull"] = binToHexRep(self.getSelectNull())
        
        self._comm.rstConnection()
        #Check if the secure-messaging is set.
        sod = None
        try:        
            sod = self._doc["SecurityData"]
            if self._comm._ciphering:
                res["bac"] = "Done"
        except Exception:
            self._comm.rstConnection()
        
        #Read SOD
        if sod != None:
            with open('sod', 'wb') as fd:
                fd.write(sod.body)
            f = os.popen("openssl asn1parse -in sod -inform DER -i")
            res["SOD"] = f.read().strip()
            os.remove('sod')
            
        #Read DGs
        self._comm.rstConnection()
        data = {}
        start = time.time()
        res["EP"]["Common"] = self._doc["Common"]
        for dg in res["EP"]["Common"]["5C"]:
            try:
                res["EP"][toDG(dg)] = self._doc[dg]
                data[toDG(dg)] = len(self._doc[dg].file)
            except Exception:
                res["failedToRead"].append(toDG(dg))
                self._comm.rstConnection()
        res["ReadingTime"] = time.time() - start
        lengths = data.items()
        lengths.sort()
        res["DGs"] = lengths
        
        # Get hashed
        dgs = list()
        for dg in res["EP"]:
            dgs.append(res["EP"][dg])
        
        #Passive Authentication
        res["Integrity"] = self._pa.executePA(sod, dgs)
        res["Hashes"] = self._pa._calculateHashes(dgs)
            
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
                    
        res["delaySecurity"] = self.checkDelaySecurity()
            
        return res
    
    def getATR(self):
        cardtype = AnyCardType()
        cardrequest = CardRequest(timeout=1, cardType=cardtype)
        cardservice = cardrequest.waitforcard()
        
        cardservice.connection.connect()
        return toHexString(cardservice.connection.getATR())
            
    def checkInternalAuth(self):
        self._comm.rstConnection()
        rnd_ifd = os.urandom(8)
        try:
            self._comm.internalAuthentication(rnd_ifd)
            return True
        except Exception:
            return False
            
    def checkMACTraceability(self):
        self._comm.rstConnection()
        attack = macTraceability.MacTraceability(self._comm)
        attack.setMRZ(str(self.curMRZ))
        return attack.isVulnerable()
    
    def checkDelaySecurity(self):
        self._comm.rstConnection()
        self._doc.doBasicAccessControl()
        self._comm.rstConnection()
        start = time.time()
        self._doc.doBasicAccessControl()
        first = time.time() - start
        rndMRZ = "AB12345671ETH0101011M1212318<<<<<<<<<<<<<<04"
        self.curMRZ = self._doc.switchMRZ(rndMRZ)
        for x in range(4):
            try:
                self._comm.rstConnection()
                self._doc.doBasicAccessControl()
            except Exception:
                pass
        self._doc.switchMRZ(self.curMRZ)
        self._comm.rstConnection()
        start = time.time()
        self._doc.doBasicAccessControl()
        if time.time() - start > 0.01:
            return True
        else: False
        
        print first-second
    
    def blockAfterFail(self):
        self._comm.rstConnection()
        rndMRZ = "AB12345671ETH0101011M1212318<<<<<<<<<<<<<<04"
        self.curMRZ = self._doc.switchMRZ(rndMRZ)
        try:
            self._doc.doBasicAccessControl()
        except Exception:
            pass
        self._doc.switchMRZ(self.curMRZ)
        try:
            self._doc.doBasicAccessControl()
        except Exception:
            return True
        return False
    
    def getSelectNull(self):
        self._comm.rstConnection()
        try:
            return self._comm.selectFile("00", "00", file="", cla="00", ins="A4")
        except Iso7816Exception, msg:
            (data, sw1, sw2) =  msg
            return "Error SW1: {} SW2:{}".format(sw1, sw2)
        return 0
    
    
    
    
