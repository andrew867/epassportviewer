# Copyright 2012 Antonin Beaujeant
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
import tkMessageBox


Errors = {  # APDU PROBLEMS
             "('Security status not satisfied', 105, 130)": 'Error #101: An error occured during the BAC.',
             "('SM data objects incorrect', 105, 136)": 'Error #102: An error occured during the BAC.',
             # READER ISSUES
             "Failed to transmit with protocol TO. Card was reset.": 'Error #201: An error occured with the reader.',
             # UNCLASSIFIED ERRORS
             "Wrong MRZ": 'Check the correct MRZ is set.',
             "sodObj must be a sod object": "Error #301: Internal error.",
             "'NoneType' object has no attribute '__getitem__'": "Error #302: Internal error."
}


def  getID(message):
    try:
        return Errors[str(message)]
    except Exception:
        print str(message)
        return "Error #404: Error has not been identified.\n{}".format(str(message))
