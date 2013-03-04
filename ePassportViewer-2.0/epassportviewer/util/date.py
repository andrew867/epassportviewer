# Copyright 2009 Jean-Francois Houzard, Olivier Roger
#
# This file is part of epassportviewer.
#
# epassportviewer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# epassportviewer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with epassportviewer.
# If not, see <http://www.gnu.org/licenses/>.

import datetime

def getDate(data=None):
    """ Convert the data into a date in the appropriate form

        @note: Return input date if no match is found
        @param data: Date of unknown size
        @type data: String
        @return: formated date
        @rtype: String
    """
    if data== None:
        return datetime.date.today().strftime("%Y-%m-%d")
    if len(data) == 6:
        return getDateYYMMDD(data)
    if len(data) == 8:
        return getDateYYYYMMDD(data)
    if len(data) == 14:
        return getDateYYYYMMDDhhmmss(data)
    return data

def getDateYYMMDD(data):
    """ Convert 840618 --> 84-06-18 """
    try:
        d = datetime.datetime(int("20"+data[:2]),int(data[2:4]),int(data[4:6])).date()
        return str(d)[2:]
    except Exception, msg:
        return data


def getDateYYYYMMDD(data):
    """ Convert 19840618 --> 1984-06-18 """
    try:
        d = datetime.datetime(int(data[:4]),int(data[4:6]),int(data[6:8])).date()
        return str(d)
    except Exception, msg:
        return data

def getDateYYYYMMDDhhmmss(data):
    """ Convert 19840618165502 --> 1984-06-18 16:55:02"""
    try:
        d = datetime.datetime(int(data[:4]),int(data[4:6]),int(data[6:8]), int(data[8:10]), int(data[10:12]), int(data[12:14]))
        return str(d.date()) + " " + str(d.time())
    except Exception, msg:
        return data