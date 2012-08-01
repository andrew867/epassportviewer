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

from Tkinter import *
import tkMessageBox
import Image, ImageTk, tkFont

from string import replace

from epassportviewer.const import *
from epassportviewer.util.configManager import configManager
from epassportviewer.util.image import convertImage, ImageFactory
from epassportviewer.util.helper import getItem

class Overview(Frame):
    
    IMAGE, SIGN = xrange(2)
    
    def __init__(self, master):
        Frame.__init__(self, master, relief=GROOVE, bd=2)
        
        self.master = master
        
        self.createLayout()
        self.bindEvents()
        
    def createLayout(self):
        container = Frame(self.master, relief=FLAT, bd=1)
        container.pack(side=TOP, fill=BOTH, expand=True)
        
        
        ###################
        ## PROFILE PHOTO ##
        self.Image = Label(container)
        self.Image.pack(side=LEFT)
        
        im = Image.open( ImageFactory().create(ImageFactory().TRANSPARENT) )
        im.thumbnail((150,150))
        Tkimage = ImageTk.PhotoImage(im)
        
        self.Image.config(image=Tkimage)
        self.Image.image = Tkimage
        
        
        ###################
        ## PERSONAL INFO ##
        
        self.fields = fields = {}
        fields['type'] = StringVar()
        fields['issueCountry'] = StringVar()
        fields['passportNumber'] = StringVar()
        fields['name'] = StringVar()
        fields['surname'] = StringVar()
        fields['nationality'] = StringVar()
        fields['sex'] = StringVar()
        fields['birthDate'] = StringVar()
        fields['birthPlace'] = StringVar()
        fields['authority'] = StringVar()
        fields['issueDate'] = StringVar()
        fields['expiryDate'] = StringVar()
        
        fields['mrz'] = StringVar()
        
        dataContainer = Frame(container, relief=RIDGE, bd=2)
        dataContainer.pack(side=TOP, fill=Y, expand=True, anchor=E, pady=2)
        
        titleFont = tkFont.Font(family="Helvetica", weight='bold', size=8)
        font = tkFont.Font(family="Helvetica", weight='normal', size=8)
        mrzFont = tkFont.Font(size=10, family='courier')
        
        # ROW 0
        row = 0
        Label(dataContainer, text="Type\t\t\t", font=titleFont).grid(row=row, column=0, columnspan=2, sticky=W)
        Label(dataContainer, text="Issuing Country\t\t\t", font=titleFont).grid(row=row, column=2, columnspan=2, sticky=W)
        Label(dataContainer, text="Passport number", font=titleFont).grid(row=row, column=4, columnspan=2, sticky=W)
        row += 1
        Label(dataContainer, textvariable=fields['type'], font=font).grid(row=row, column=0, columnspan=2, sticky=W)
        Label(dataContainer, textvariable=fields['issueCountry'], font=font).grid(row=row, column=2, columnspan=2, sticky=W)
        Label(dataContainer, textvariable=fields['passportNumber'], font=font).grid(row=row, column=4, columnspan=2, sticky=W)
        
        # ROW 2
        row += 1
        Label(dataContainer, text="Name", font=titleFont).grid(row=row, column=0, columnspan=6, sticky=W)
        row += 1
        Label(dataContainer, textvariable=fields['name'], font=font).grid(row=row, column=0, columnspan=6, sticky=W)
        
        # ROW 4
        row += 1
        Label(dataContainer, text="Surname", font=titleFont).grid(row=row, column=0, columnspan=6, sticky=W)
        row += 1
        Label(dataContainer, textvariable=fields['surname'], font=font).grid(row=row, column=0, columnspan=6, sticky=W)
        
        # ROW 6
        row += 1
        Label(dataContainer, text="Nationality", font=titleFont).grid(row=row, column=0, columnspan=6, sticky=W)
        row += 1
        Label(dataContainer, textvariable=fields['nationality'], font=font).grid(row=row, column=0, columnspan=6, sticky=W)
        
        # ROW 8
        row += 1
        Label(dataContainer, text="Date of birth", font=titleFont).grid(row=row, column=0, columnspan=3, sticky=W)
        Label(dataContainer, text="Place of birth", font=titleFont).grid(row=row, column=3, columnspan=3, sticky=W)
        row += 1
        Label(dataContainer, textvariable=fields['birthDate'], font=font).grid(row=row, column=0, columnspan=3, sticky=W)
        Label(dataContainer, textvariable=fields['birthPlace'], font=font).grid(row=row, column=3, columnspan=3, sticky=W)
        
        # ROW 10
        row += 1
        Label(dataContainer, text="Sex", font=titleFont).grid(row=row, column=0, columnspan=3, sticky=W)
        Label(dataContainer, text="Authority", font=titleFont).grid(row=row, column=3, columnspan=3, sticky=W)
        row += 1
        Label(dataContainer, textvariable=fields['sex'], font=font).grid(row=row, column=0, columnspan=3, sticky=W)
        Label(dataContainer, textvariable=fields['authority'], font=font).grid(row=row, column=3, columnspan=3, sticky=W)
        
        # ROW 12
        row += 1
        Label(dataContainer, text="Date of issue", font=titleFont).grid(row=row, column=0, columnspan=3, sticky=W)        
        Label(dataContainer, text="Signature", font=titleFont).grid(row=row, column=3, columnspan=3, sticky=W)
        row += 1
        
        self.Sign = Label(dataContainer)
        self.Sign.grid(row=row, rowspan=3, column=3, columnspan=3)
        
        im = Image.open( ImageFactory().create(ImageFactory().TRANSPARENT) )
        im.thumbnail((200,150))
        Tkimage = ImageTk.PhotoImage(im)
        
        self.Sign.config(image=Tkimage)
        self.Sign.image = Tkimage
        
        Label(dataContainer, textvariable=fields['issueDate'], font=font).grid(row=row, column=0, columnspan=6, sticky=W)
        row += 1
        
        # ROW 14
        Label(dataContainer, text="Date of Expiry", font=titleFont).grid(row=row, column=0, columnspan=3, sticky=W)
        row += 1
        Label(dataContainer, textvariable=fields['expiryDate'], font=font).grid(row=row, column=0, columnspan=3, sticky=W)
        
        
        #################
        ## MRZ LOG BOX ##
        
        mrzContainer = Frame(self.master, bd=2, relief=GROOVE)
        mrzContainer.pack(side=TOP, fill=BOTH, expand=True, anchor=CENTER)
        Label(mrzContainer, textvariable=fields['mrz'], bg='white', font=mrzFont).pack(side=LEFT, fill=BOTH, expand=True)
        
        
        ##########
        ## PACK ##
        
        for type in [self.SIGN, self.IMAGE]:
            self.updatePicture( ImageFactory().create(ImageFactory().TRANSPARENT), type)

        self.update()
        
    def updatePicture(self, path, type):
        im=Image.open(path)
        
        if type == self.SIGN:
            im.thumbnail((180,180))
        if type == self.IMAGE:
            im.thumbnail((275,275))
            
        Tkimage = ImageTk.PhotoImage(im)
        if type == self.IMAGE: 
            self.Image.config(image=Tkimage)
            self.Image.image = Tkimage
        if type == self.SIGN:
            self.Sign.config(image=Tkimage)
            self.Sign.image = Tkimage
            
    def loadDG1(self, fields, data):
        if data.has_key('5F1F'): 
            mrz = data['5F1F']
            mrz = mrz[:44] + "\n" + mrz[44:]
            if len(data['5F1F']) > 88:
                mrz = mrz[:89] + "\n" + mrz[89:]
            fields['mrz'].set(mrz)

        if data.has_key('5F5B'):
            name = (data['5F5B']).split("<<")
            fields['name'].set(getItem(name[0]))
            fields['surname'].set(getItem(name[1]))
        
        if data.has_key('5F03'):
            fields['type'].set(getItem(data['5F03']))
        if data.has_key('5F28'):
            fields['issueCountry'].set(getItem(data['5F28']))
        if data.has_key('5A'):
            fields['passportNumber'].set(getItem(data['5A']))
        if data.has_key('5F2C'):
            fields['nationality'].set(getItem(data['5F2C']))
        if data.has_key('5F57'):
            fields['birthDate'].set(getItem(data['5F57']))
        if data.has_key('5F35'):
            fields['sex'].set(getItem(data['5F35']))
        if data.has_key('59'):
            fields['expiryDate'].set(getItem(data['59']))         
    
    def loadDG2(self, fields, data):
        tag = None
        if data['A1'].has_key('5F2E'): tag = '5F2E'
        elif data['A1'].has_key('7F2E'): tag = '7F2E'
        if tag != None:
            stream = convertImage(data['A1'][tag])
            try:
                self.updatePicture(stream, self.IMAGE)
            except Exception, msg:
                tkMessageBox.showwarning("Image Error", str(msg))
            
    def loadDG7(self, fields, data):
        if data.has_key('5F43'):
            try:
                stream = convertImage(data['5F43'][0])
                self.updatePicture(stream, self.SIGN)
            except Exception, msg:
                tkMessageBox.showwarning("Image Error", str(msg))

    def loadDG11(self, fields, data):
        if data.has_key("5F11"):
            fields['birthPlace'].set(getItem(data['5F11']))
        
    def loadDG12(self, fields, data):
        if data.has_key("5F19"):
            fields['authority'].set(getItem(data['5F19']))
        if data.has_key("5F26"):
            fields['issueDate'].set(getItem(data['5F26']))       
                 
    def loadDG(self, dg, data):
            
        if dg in ["61", "67", "6B", "6C", "75"]:
            if dg == "61": self.loadDG1(self.fields, data)
            elif dg == "75": self.loadDG2(self.fields, data)
            elif dg == "67": self.loadDG7(self.fields, data)
            elif dg == "6B": self.loadDG11(self.fields, data)
            elif dg == "6C": self.loadDG12(self.fields, data)
            
        self.update()
                
    def clear(self):
        for field in self.fields:
            self.fields[field].set("")
        for type in [self.SIGN, self.IMAGE]:
            self.updatePicture( ImageFactory().create(ImageFactory().TRANSPARENT), type)
    
    def bindEvents(self):
        pass
    
