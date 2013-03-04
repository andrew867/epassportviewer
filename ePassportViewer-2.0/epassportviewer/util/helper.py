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

from string import replace
from epassportviewer.util.date import getDate

def getItem(value):
    """ remove the < character from data and improve date visualisation
    
        @param value: Value to clean
        @type value: String
        @return: cleaned value
        @rtype: String
    """
    try:
        if value == None:
            return
        value = replace(value,"<"," ")
        value = getDate(value)
        return str(value)
    except Exception, msg:
        return ""  
    
def getItemByTag(dic, *tags):
    value = dic
    for tag in tags:
        if value.has_key(tag):
            value = value[tag]
        else: return None
        
    return getItem(value)

    
def getItemRaw(dic, *tags):
    value = dic
    for tag in tags:
        if value.has_key(tag):
            value = value[tag]
        else: return None
        
    try:
        if len(value) > 50:
            value = split_len(value, 44)
        value = replace(value,"<","&lt;")
    except Exception, msg:
        return ""
        
    return str(value)


def split_len(seq, length):
    list_str = list()
    for i in range(0, len(seq), length):
        list_str.append(seq[i:i+length])
    return ' '.join(list_str)
        

