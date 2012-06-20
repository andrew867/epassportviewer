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

import datetime
import pickle
import os

from pypassport.logger import Logger
from pypassport.iso7816 import Iso7816, Iso7816Exception 
from pypassport.reader import PcscReader, ReaderException
from pypassport import apdu
from pypassport.iso9797 import *
from pypassport.hexfunctions import hexToHexRep, binToHexRep

class ErrorFingerprintingException(Exception):
    def __init__(self, *params):
        Exception.__init__(self, *params)

class ErrorFingerprinting(Logger):
    """
    ICAO described minimum required instruction for the communication between the reader and the passport.
    Therefore, regarding features implemented, a passport might behave in a different way with a different error message
    This lack of a standartisation create a fingerprint an attacker could use to identify the issuer and the version of the passport.
    This class implement methods in order to store error regarding the country and the version and identify a passport.
    """

    def __init__(self, iso7816, path="error.dat"):
        Logger.__init__(self, "ERROR FINGERPRINTING")
        self._iso7816 = iso7816
        
        if type(self._iso7816) != type(Iso7816(None)):
            raise MacTraceabilityException("The sublayer iso7816 is not available")

        self._iso7816.rstConnection()
        
        self._path = path
        
        if os.path.exists(path):
            with open(path, 'rb') as file_errors:
                my_unpickler = pickle.Unpickler(file_errors)
                self.errors = my_unpickler.load()
        else:
            self.errors = { "0000000000": { "0x6d 0x0": {   "BEL": ["2009", "2011"], 
                                                            "FRA": ["2010"]
                                                        }
                                          }
                          }
    
    def sendCustom(self, cla="00", ins="00", p1="00", p2="00", lc="", data="", le="00"):
        """
        Send custom APDU in order to trigger errors.
        
        @param cla, ins, p1, p2, lc, data, le: APDU value
        @type cla, ins, p1, p2, lc, data, le: String of 2hex (from 00 to FF) except lc and date that may be an empty String
        
        @return: A set composed of boolean (True=Succeed, False=Error) and a passport answer
        """

        toSend = apdu.CommandAPDU(cla, ins, p1, p2, lc, data, le)
        
        try:
            self.log("Send APDU: {0}:{1}:{2}:{3}:{4}:{5}:{6}".format(cla, ins, p1, p2, lc, data, le))
            ans = self._iso7816.transmit(toSend, "Custom APDU")   
            return (True, binToHexRep(ans))
        except Iso7816Exception, msg:
            return (False, msg)
    
    def addError(self, new_query, ans, new_country, year=str(datetime.datetime.today().year)):
        """
        Add in the error dictionnary (self.errors + save in file) a set composed of:
         - The APDU sent
         - The error received
         - Issuer (country)
         - The version (year)
        
        @param new_query: The APDU sent
        @type new_query: String of 10 to 14 hex
        @param ans: The answer from the passport
        @type ans: A set composed of boolean (True=Succeed, False=Error) and a passport answer
        @param new_country: The issuer (country)
        @type new_country: String of 3 char (Official country id)
        @param year: The passport version (date of issue)
        @type year: String of 4 digits (i.e. "2012")
        """

        (valide, err) = ans
        if valide==True:
            print new_query
            raise ErrorFingerprintingException("The query triggered no error")
        (error_text, nb1, nb2) = err
        new_error = "{0} {1}".format(hex(nb1), hex(nb2))
        i=True
        for query in self.errors:
            if query==new_query:
                for error in self.errors[query]:
                    if error==new_error:
                        for country in self.errors[query][error]:
                            if country==new_country:
                                for date in self.errors[query][error][country]:
                                    if date==year:
                                        self.log("The entry already exist")
                                        i=False
                                if i:
                                    self.errors[new_query][new_error][new_country].append(year)
                                    self.log("The entry has been added")
                                    i=False
                        if i:
                            self.errors[new_query][new_error][new_country] = [year]
                            self.log("The entry has been added")
                            i=False
                if i:
                    self.errors[new_query][new_error] = { new_country: [year] } 
                    self.log("The entry has been added")
                    i=False
        if i:
            self.errors[new_query] = { new_error: { new_country: [year] } }
            self.log("The entry has been added")
            i=False
        
        with open(self._path, 'wb') as file_errors:
            self.log("Save the dictionnary")
            my_pickler = pickle.Pickler(file_errors)
            my_pickler.dump(self.errors)
    
    def identify(self, cla="00", ins="00", p1="00", p2="00", lc="", data="", le="00"):
        """
        Identify a passport by sending a custom APDU and checking the answer in the error dictionnary
        
        @param cla, ins, p1, p2, lc, data, le: APDU value
        @type cla, ins, p1, p2, lc, data, le: String of 2hex (from 00 to FF) except lc and date that may be an empty String

        @raise ErrorFingerprintingException: If the query triggered no error, it raise an error
        
        @return: Return all the possible issuer-version the passport might belongs to.
        """

        cur_query = cla + ins + p1 + p2 + lc + data + le
        (valide, err) = self.sendCustom(cla, ins, p1, p2, lc, data, le)
        if valide==True:
            raise ErrorFingerprintingException("Not possible to identify the passport since the query is correct")
        (error_text, nb1, nb2) = err
        new_error = "{0} {1}".format(hex(nb1), hex(nb2))
        possibilities = list()
        
        self.log("Check for error: {0}".format(new_error))
        for query in self.errors:
            if query==cur_query:
                for error in self.errors[query]:
                    if error==new_error:
                        for country in self.errors[query][error]:
                            cur_country = country
                            for date in self.errors[query][error][country]:
                                possibilities.append("{0} {1}".format(cur_country, date))
        
        return possibilities
    










