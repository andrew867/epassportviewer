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
from pypassport import iso7816, apdu, camanager
from pypassport.hexfunctions import *
from pypassport.doc9303.converter import *
from pypassport.apdu import CommandAPDU
from pypassport.attacks import macTraceability
from pypassport.epassport import EPassportException

from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.util import toHexString

class FingerPrint(object):
    
    def __init__(self, epassport, certdir=None, callback=None):
        self._doc = epassport
        self.curMRZ = None
        self._comm = self._doc.getCommunicationLayer()
        self._pa = passiveauthentication.PassiveAuthentication(epassport)
        self._certInfo = None
        self.callback = callback
        self.doPA = False
        
        if certdir:
            try:
                self.csca = camanager.CAManager(certdir)
                self.csca.toHashes()
                self.doPA = True
            except Exception:
                pass
        
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
        res["getChallengeNull"] = "N/A"
        res["bac"] = "Failed"
        res["verifySOD"] = "No certificate imported"
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
        res["Errors"] = dict()
        
        
        # GET UID
        if self.callback: 
            self.callback.put((None, 'slfp', "Get UID"))
            self.callback.put((None, 'fp', 5))
        
        try:
            res["UID"] = binToHexRep(self._comm.getUID())
        except Exception, msg:
            pass
        
        # GET ATR
        if self.callback: 
            self.callback.put((None, 'slfp', "Get ATR"))
            self.callback.put((None, 'fp', 10))
        
        try:
            res["ATR"] = self.getATR()
        except Exception, msg:
            pass
        
        # Check if passport block after the BAC fail
        if self.callback: 
            self.callback.put((None, 'slfp', "Check if block after BAC failed"))
            self.callback.put((None, 'fp', 15))
        
        res["blockAfterFail"] = self.blockAfterFail()
        
        # Check if AA is possible before BAC
        if self.callback: 
            self.callback.put((None, 'slfp', "Check AA before BAC"))
            self.callback.put((None, 'fp', 20))
        
        res["activeAuthWithoutBac"] = self.checkInternalAuth()
        
        # Check if passport is vulnerable to MAC traceability
        if self.callback: 
            self.callback.put((None, 'slfp', "Check MAC traceability"))
            self.callback.put((None, 'fp', 25))
        
        res["macTraceability"] = self.checkMACTraceability()
        
        # Send a SELECT FILE null and check the answer
        if self.callback: 
            self.callback.put((None, 'slfp', "Check select application null"))
            self.callback.put((None, 'fp', 30))
        
        # Send a GET CHALLENGE with Le set to 00
        if self.callback: 
            self.callback.put((None, 'slfp', "Check Get Challenge length 00"))
            self.callback.put((None, 'fp', 35))
        
        res["getChallengeNull"] = self.sendGetChallengeNull()
        
        #Check if the secure-messaging is set (BAC)
        #(Get SOD)
        if self.callback: 
            self.callback.put((None, 'slfp', "Check BAC"))
            self.callback.put((None, 'fp', 40))
        
        self._comm.rstConnection()
        sod = None
        try:        
            sod = self._doc["SecurityData"]
            if self._comm._ciphering:
                res["bac"] = "Done"
        except Exception, msg:
            self._comm.rstConnection()
            raise Exception(msg)
        
        #Read SOD body
        if self.callback: 
            self.callback.put((None, 'slfp', "Read SOD"))
            self.callback.put((None, 'fp', 45))
            
        if sod != None:
            with open('sod', 'wb') as fd:
                fd.write(sod.body)
            f = os.popen("openssl asn1parse -in sod -inform DER -i")
            res["SOD"] = f.read().strip()
            os.remove('sod')
            
            #Verify SOD body
            if self.callback: 
                self.callback.put((None, 'slfp', "Verify SOD with CSCA"))
                self.callback.put((None, 'fp', 50))
            
            if self.doPA:
                try:
                    pa = passiveauthentication.PassiveAuthentication()
                    res["verifySOD"] = pa.verifySODandCDS(sod, self.csca)
                except Exception:
                    res["verifySOD"] = "No certificate imported verify the SOD"
                    pass
        
        #Read DGs and get the file content
        if self.callback: 
            self.callback.put((None, 'slfp', "Read DGs"))
            self.callback.put((None, 'fp', 55))
            
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
        if self.callback: 
            self.callback.put((None, 'slfp', "Get hashes of DG files"))
            self.callback.put((None, 'fp', 65))
            
        dgs = list()
        for dg in res["EP"]:
            dgs.append(res["EP"][dg])
        
        res["Integrity"] = self._pa.executePA(sod, dgs)
        res["Hashes"] = self._pa._calculateHashes(dgs)
            
        #Check if there is a certificate
        if self.callback: 
            self.callback.put((None, 'slfp', "Proceed to AA"))
            self.callback.put((None, 'fp', 70))
            
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
        if self.callback: 
            self.callback.put((None, 'slfp', "Get public key"))
            self.callback.put((None, 'fp', 80))
        try:
            self._comm.rstConnection()
            if self._doc.getPublicKey():
                res["pubKey"] = self._doc.getPublicKey()
            if self._doc.doActiveAuthentication():
                res["activeAuth"] = "Done"
        except Exception, msg:
            pass
        
        # Define generation
        if self.callback: 
            self.callback.put((None, 'slfp', "Define the generation"))
            self.callback.put((None, 'fp', 85))

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
        
        
        # Check if passport implement delay security
        if self.callback: 
            self.callback.put((None, 'slfp', "Check delay security is implemented"))
            self.callback.put((None, 'fp', 90))
            
        res["delaySecurity"] = self.checkDelaySecurity()
        
        # Get error message from different wrong APDU
        if self.callback: 
            self.callback.put((None, 'slfp', "Get a sample of error message"))
            self.callback.put((None, 'fp', 95))
            
        res["Errors"] = self.getErrorsMessage()
            
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
            return (True, binToHexRep(self._comm.internalAuthentication(rnd_ifd)))
        except Iso7816Exception, msg:
            (data, sw1, sw2) =  msg
            return (False, "SW1:{} SW2:{}".format(sw1, sw2))
            
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
        second = time.time() - start
        if second - first > 0.01:
            return True
        else: return False
        
    
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
    
    def sendGetChallengeNull(self):
        self._comm.rstConnection()
        try:
            toSend = apdu.CommandAPDU("00", "84", "00", "00", "", "", "01")   
            return (True, binToHexRep(self._comm.transmit(toSend, "Select File")))
        except Iso7816Exception, msg:
            (data, sw1, sw2) =  msg
            return (False, "SW1:{} SW2:{}".format(sw1, sw2))
        return "N/A"
    
    def getErrorsMessage(self):
        test = ["44", "82", "84", "88", "A4", "B0", "B1"]
        errors = dict()
        for ins in test:
            self._comm.rstConnection()
            try:
                toSend = apdu.CommandAPDU("00", ins, "00", "00", "", "", "00")
                self._comm.transmit(toSend, "Select File")
                errors[ins] = "SW1:{} SW2:{}".format(144, 0)
            except Iso7816Exception, msg:
                (data, sw1, sw2) =  msg
                errors[ins] = "SW1:{} SW2:{}".format(sw1, sw2)
        return errors
        
        
