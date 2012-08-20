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

    
_Errors = {  "('Security status not satisfied', 105, 130)": ('Error #101: The passport requires to first establish the connection with a valid BAC.', "error")
    }
    
    
def  showError(message="Empty", title="Error"):
    try:
        error, symbol = Errors[str(message)]
        if symbol == "error":
            tkMessageBox.showerror(title, error)
        if symbol == "warning":
            tkMessageBox.showwarning(title, error)
        if symbol == "info":
            tkMessageBox.showinfo(title, error)
    except Exception:
        tkMessageBox.showerror("Error not identify", "Error #404: Error has not been identify.\n{}".format(message))
