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

try:
    import pygtk
    pygtk.require('2.0')
    import gtk
except:
    GTK = False

from Tkinter import *
import tkMessageBox
import thread
import threading
import tkFont
from PIL import Image, ImageTk
import Queue
import time
import re
from tkFileDialog import askdirectory, askopenfilename, asksaveasfilename

from epassportviewer.const import *
from epassportviewer.util import forge, inOut
from epassportviewer.util.image import ImageFactory
from epassportviewer.util.components import DataGroupGridList
from epassportviewer.util.configManager import configManager
from epassportviewer import errorhandler

from pypassport import epassport
from pypassport import fingerPrint
from pypassport.hexfunctions import *
from pypassport.doc9303 import datagroup
from pypassport.doc9303.datagroup import *
from pypassport.doc9303.converter import *
from pypassport.doc9303.tagconverter import *
from pypassport.doc9303.bac import BACException

class create(Toplevel):

    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.title("Create a passport (JCOP)")
        self.resizable(False,False)
        self.transient(master)
        self.master = master

        ##########
        #  VIEW  #
        ##########

        title = tkFont.Font(size=12)

        createFrame = Frame(self, borderwidth=1, relief=GROOVE)
        createFrame.pack(fill=BOTH, expand=1)

        # HOLDER'S INFORTMATION
        holderLabel = Label(createFrame, text="Holder's information:", justify=LEFT, font=title)
        holderLabel.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=(N, W))

        # Firstname
        firstnameLabel = Label(createFrame, text="Firstname:", justify=LEFT)
        firstnameLabel.grid(row=1, column=0, padx=5, pady=5, sticky=(N, W))

        self.firstnameForm = Entry(createFrame, width=30)
        self.firstnameForm.grid(row=1, column=1, padx=5, pady=5, sticky=(N, W))

        # Surname
        surnameLabel = Label(createFrame, text="Surname:", justify=LEFT)
        surnameLabel.grid(row=2, column=0, padx=5, pady=5, sticky=(N, W))

        self.surnameForm = Entry(createFrame, width=30)
        self.surnameForm.grid(row=2, column=1, padx=5, pady=5, sticky=(N, W))

        # Sex
        sexLabel = Label(createFrame, text="Sex:", justify=LEFT)
        sexLabel.grid(row=3, column=0, padx=5, pady=5, sticky=(N, W))

        sexFrame = Frame(createFrame)
        sexFrame.grid(row=3, column=1, sticky=(N, W))

        self.sex = StringVar()
        self.sex.set("M")

        maleRadio = Radiobutton(sexFrame, text="M", variable=self.sex, value="M")
        maleRadio.pack(side=LEFT, padx=5, pady=5, anchor=W)

        femaleRadio = Radiobutton(sexFrame, text="F", variable=self.sex, value="F")
        femaleRadio.pack(side=LEFT, padx=5, pady=5, anchor=W)

        # Date of birth
        dobLabel = Label(createFrame, text="Date of birth:", justify=LEFT)
        dobLabel.grid(row=4, column=0, padx=5, pady=5, sticky=(N, W))

        self.dobForm = Entry(createFrame, width=10, justify=LEFT)
        self.dobForm.grid(row=4, column=1, padx=5, pady=5, sticky=(N, W))
        self.dobForm.insert(0, "YYYY/MM/DD")

        # Nationality
        nationalityLabel = Label(createFrame, text="Nationality:", justify=LEFT)
        nationalityLabel.grid(row=5, column=0, padx=5, pady=5, sticky=(N, W))

        self.nationalityForm = Entry(createFrame, width=3, justify=LEFT)
        self.nationalityForm.grid(row=5, column=1, padx=5, pady=5, sticky=(N, W))

        documentLabel = Label(createFrame, text="Document's information:", justify=LEFT, font=title)
        documentLabel.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky=(N, W))

        # Id
        idLabel = Label(createFrame, text="ID:", justify=LEFT)
        idLabel.grid(row=7, column=0, padx=5, pady=5, sticky=(N, W))

        self.idForm = Entry(createFrame, width=9, justify=LEFT)
        self.idForm.grid(row=7, column=1, padx=5, pady=5, sticky=(N, W))

        # Expiration data
        doeLabel = Label(createFrame, text="Expiration date:", justify=LEFT)
        doeLabel.grid(row=8, column=0, padx=5, pady=5, sticky=(N, W))

        self.doeForm = Entry(createFrame, width=10, justify=LEFT)
        self.doeForm.grid(row=8, column=1, padx=5, pady=5, sticky=(N, W))
        self.doeForm.insert(0, "YYYY/MM/DD")

        # Issuer
        issuerLabel = Label(createFrame, text="Issuer:", justify=LEFT)
        issuerLabel.grid(row=9, column=0, padx=5, pady=5, sticky=(N, W))

        self.issuerForm = Entry(createFrame, width=3, justify=LEFT)
        self.issuerForm.grid(row=9, column=1, padx=5, pady=5, sticky=(N, W))

        # Face
        issuerLabel = Label(createFrame, text="Face:", justify=LEFT, font=title)
        issuerLabel.grid(row=10, column=0, columnspan=2, padx=5, pady=5, sticky=(N, W))

        faceFrame = Frame(createFrame)
        faceFrame.grid(row=11, column=0, columnspan=2, sticky=(N, W))

        selectImageButton = Button(faceFrame, text="Select image...", width=10, command=self.selectImage)
        selectImageButton.pack(side=LEFT, padx=5, pady=5)

        self.faceForm = Entry(faceFrame, width=30, justify=LEFT)
        self.faceForm.pack(side=LEFT, padx=5, pady=5)

        # CERTIFICATE
        certificateLabel = Label(createFrame, text="Certificate:", justify=LEFT, font=title)
        certificateLabel.grid(row=12, column=0, columnspan=2, padx=5, pady=5, sticky=(N, W))

        countryLabel = Label(createFrame, text="Country:", justify=LEFT)
        countryLabel.grid(row=13, column=0, padx=5, pady=5, sticky=(N, E))

        self.countryForm = Entry(createFrame, width=2, justify=LEFT)
        self.countryForm.grid(row=13, column=1, padx=5, pady=5, sticky=(N, W))

        organisationLabel = Label(createFrame, text="Organisation:", justify=LEFT)
        organisationLabel.grid(row=14, column=0, padx=5, pady=5, sticky=(N, E))

        self.organisationForm = Entry(createFrame, width=3, justify=LEFT)
        self.organisationForm.grid(row=14, column=1, padx=5, pady=5, sticky=(N, W))

        # GENERATE
        #buttonsFrame = Frame(createFrame)
        #buttonsFrame.grid(row=15, column=0, columnspan=2)

        generateButton = Button(createFrame, text="Generate...", width=43, command=self.actionGenerate)
        generateButton.grid(row=15, column=0, columnspan=2, padx=5, pady=5)

        updateButton = Button(createFrame, text="Update", width=43, command=self.actionUpdate)
        updateButton.grid(row=15, column=2, columnspan=2, padx=5, pady=5)

        # OPTIONAL
        holderLabel = Label(createFrame, text="Optional:", justify=LEFT, font=title)
        holderLabel.grid(row=0, column=2, columnspan=2, padx=5, pady=5, sticky=(N, W))

        # Place of birth
        pobLabel = Label(createFrame, text="Place of birth:", justify=LEFT)
        pobLabel.grid(row=1, column=2, padx=5, pady=5, sticky=(N, W))

        self.pobForm = Entry(createFrame, width=30)
        self.pobForm.grid(row=1, column=3, padx=5, pady=5, sticky=(N, W))

        # Middle name
        middleLabel = Label(createFrame, text="Middle name:", justify=LEFT)
        middleLabel.grid(row=2, column=2, padx=5, pady=5, sticky=(N, W))

        self.middleForm = Entry(createFrame, width=30)
        self.middleForm.grid(row=2, column=3, padx=5, pady=5, sticky=(N, W))

        # Issuing authority
        issuingAuthLabel = Label(createFrame, text="Issuing authority:", justify=LEFT)
        issuingAuthLabel.grid(row=3, column=2, padx=5, pady=5, sticky=(N, W))

        self.issuingAuthForm = Entry(createFrame, width=30)
        self.issuingAuthForm.grid(row=3, column=3, padx=5, pady=5, sticky=(N, W))

        # Date of issue
        doiLabel = Label(createFrame, text="Date of issue:", justify=LEFT)
        doiLabel.grid(row=4, column=2, padx=5, pady=5, sticky=(N, W))

        self.doiForm = Entry(createFrame, width=10, justify=LEFT)
        self.doiForm.grid(row=4, column=3, padx=5, pady=5, sticky=(N, W))
        self.doiForm.insert(0, "YYYY/MM/DD")

        # Height
        heightLabel = Label(createFrame, text="Height:", justify=LEFT)
        heightLabel.grid(row=5, column=2, padx=5, pady=5, sticky=(N, W))

        self.heightForm = Entry(createFrame, width=30)
        self.heightForm.grid(row=5, column=3, padx=5, pady=5, sticky=(N, W))

        # Eyes
        eyesLabel = Label(createFrame, text="Eyes:", justify=LEFT)
        eyesLabel.grid(row=6, column=2, padx=5, pady=5, sticky=(N, W))

        self.eyesForm = Entry(createFrame, width=30)
        self.eyesForm.grid(row=6, column=3, padx=5, pady=5, sticky=(N, W))


        # Address
        addressLabel = Label(createFrame, text="Address:", justify=LEFT)
        addressLabel.grid(row=8, column=2, padx=5, pady=5, sticky=(N, W))

        self.addressForm = Entry(createFrame, width=30)
        self.addressForm.grid(row=8, column=3, padx=5, pady=5, sticky=(N, W))



    ################
    #  CONTROLLER  #
    ################

    def selectImage(self):
        try:
            filename = askopenfilename(title="Select image")
            if filename:
                filename = str(filename)
                if os.path.isfile(filename):
                    self.faceForm.insert(0, filename)
                else:
                    tkMessageBox.showerror("Error: save", "The path you selected is not a file")
        except Exception, msg:
            tkMessageBox.showerror("Error: save", str(msg))

    def actionUpdate(self):

        forge.generate( firstname = self.firstnameForm.get(),
                        surname = self.surnameForm.get(),
                        sex = self.sex.get(),
                        dob = self.dobForm.get(),
                        nationality = self.nationalityForm.get(),
                        id_doc= self.idForm.get(),
                        doe = self.doeForm.get(),
                        issuer = self.issuerForm.get(),
                        face_path = self.faceForm.get(),
                        country = self.countryForm.get(),
                        organisation = self.organisationForm.get(),
                        pob = self.pobForm.get(),
                        middle_name = self.middleForm.get(),
                        issuing_auth = self.issuingAuthForm.get(),
                        doi = self.doiForm.get(),
                        height = self.heightForm.get(),
                        eyes = self.eyesForm.get(),
                        address = self.addressForm.get()
                      )

        tkMessageBox.showinfo("Update done", "The update has been done")

    def actionGenerate(self):
        try:
            filename = askopenfilename(title="Select epassport.cap")
            if filename:
                filename = str(filename)
                if os.path.isfile(filename):

                    forge.generate( firstname = self.firstnameForm.get(),
                                    surname = self.surnameForm.get(),
                                    sex = self.sex.get(),
                                    dob = self.dobForm.get(),
                                    nationality = self.nationalityForm.get(),
                                    id_doc= self.idForm.get(),
                                    doe = self.doeForm.get(),
                                    issuer = self.issuerForm.get(),
                                    face_path = self.faceForm.get(),
                                    country = self.countryForm.get(),
                                    organisation = self.organisationForm.get(),
                                    pob = self.pobForm.get(),
                                    middle_name = self.middleForm.get(),
                                    issuing_auth = self.issuingAuthForm.get(),
                                    doi = self.doiForm.get(),
                                    height = self.heightForm.get(),
                                    eyes = self.eyesForm.get(),
                                    address = self.addressForm.get(),
                                    update = False,
                                    cap_path = filename
                                  )

                    tkMessageBox.showinfo("Generation done", "The ePassport has been generated")

                else:
                    tkMessageBox.showerror("Error: save", "The path you selected is not a file")
        except Exception, msg:
            tkMessageBox.showerror("Error: generate", str(msg))





class WaitDialog(Toplevel):

    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.title("Please wait")
        self.resizable(False,False)
        self.transient(master)
        self.grab_set()

        self.waitFrame = Frame(self)
        self.waitFrame.pack(fill=BOTH, expand=1)

        self.txt = StringVar()
        self.txt.set("Please wait...")
        self.waitLabel = Label(self.waitFrame, textvariable=self.txt, justify=LEFT)
        self.waitLabel.pack(padx=20, pady=20)

    def closeDialog(self):
        self.destroy()

    def setMessage(self, message):
        self.txt.set(message)
        self.update()
        self.deiconify()





class About(Toplevel):

    VERSIONTEXT = "Version " + VERSION

    DESCRIPTION = """ePassport Viewer is a biometric passport viewer.\n\
This application is based on the pyPassport Project\n\
and illustrates how to use it.\n\
Features include viewing data, fingerprinting and\n\
performing e-Passport security mechanisms."""

    PLACE = "Universite Catholique de Louvain (UCL) @ 2009"
    GROUP = "http://sites.uclouvain.be/security/"

    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.title("About")
        self.resizable(False,False)
        self.transient(master)
        self.grab_set()

        epvFrame = Frame(self, borderwidth=1)
        epvFrame.pack(fill=BOTH, expand=1)

        Label(epvFrame, text="ePassport Viewer", font=(None, 16, 'bold')).grid(row=0, column=0, columnspan=2, padx=20, pady=5, sticky=W)

        im = Image.open(ImageFactory().create(ImageFactory().LOGO))
        image = ImageTk.PhotoImage(im)
        img = Label(epvFrame, image=image, anchor=CENTER)
        img.image = image
        img.grid(row=1, column=0, padx=20, pady=5)

        Label(epvFrame, text=self.DESCRIPTION, justify=LEFT).grid(row=1, column=1, padx=5, sticky=NW)

        Label(epvFrame, text=self.VERSIONTEXT, anchor=CENTER).grid(row=2, column=0, padx=5)


        devFrame = Frame(self, borderwidth=1)
        devFrame.pack(fill=BOTH, expand=1, pady=20)

        Label(devFrame, text="Developer", font=(None, 16, 'bold')).grid(row=0, column=0, columnspan=2, padx=20, pady=5, sticky=W)

        im = Image.open(ImageFactory().create(ImageFactory().NEWGSI))
        image = ImageTk.PhotoImage(im)
        img = Label(devFrame, image=image, anchor=CENTER)
        img.image = image
        img.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

        Label(devFrame, text="Version 1.0", font=(None, 9, 'bold')).grid(row=2, column=0, columnspan=2, padx=20, sticky=W)

        Label(devFrame, text="Jean Francois HOUZARD").grid(row=3, column=0, padx=20, sticky=W)
        Label(devFrame, text="email: jhouzard@gmail.com").grid(row=3, column=1, padx=5, sticky=W)

        Label(devFrame, text="Olivier ROGER").grid(row=4, column=0, padx=20, sticky=W)
        Label(devFrame, text="email: olivier.roger@gmail.com").grid(row=4, column=1, padx=5, sticky=W)

        Label(devFrame, text="Version 2.0", font=(None, 9, 'bold')).grid(row=5, column=0, columnspan=2, padx=20, sticky=W)

        Label(devFrame, text="Antonin BEAUJEANT").grid(row=6, column=0, padx=20, sticky=W)
        Label(devFrame, text="email: antonin.beaujeant@gmail.com").grid(row=6, column=1, padx=5, sticky=W)


        licenseFrame = Frame(self, borderwidth=1)
        licenseFrame.pack(fill=BOTH, expand=1)

        Label(licenseFrame, text="License", font=(None, 16, 'bold')).grid(row=0, column=0, columnspan=2, padx=20, pady=5, sticky=W)

        im = Image.open(ImageFactory().create(ImageFactory().GPLV3))
        image = ImageTk.PhotoImage(im)
        img = Label(licenseFrame, image=image, anchor=CENTER)
        img.image = image
        img.grid(row=1, column=0, padx=20, pady=10)

        Button(licenseFrame, text="GNU/LGPL v3", command=self.clickLicense).grid(row=1, column=1, padx=30, pady=5)


    def clickLicense(self):
        if os.path.isfile(LICENSE):
            License(self)
        else:
            tkMessageBox.showinfo("No License File", "There is no license file available")


class License(Toplevel):
    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.title("License GNU/GPL v3")
        self.transient(master)
        self.grab_set()

        file = open(LICENSE,'r')
        self.txt = file.read()
        file.close()

        log = ScrollFrame(self, self.txt)
        log.pack(side=TOP, fill=BOTH, expand=True)



class Log(Toplevel):
    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.title("Log")
        self.transient(master)
        self.grab_set()

        self.logFrame = ScrollFrame(self)
        self.logFrame.pack(side=TOP, fill=BOTH, expand=True)

        self.epCheck = BooleanVar()
        self.epCheck.set(configManager().getOption('Logs','api'))
        ep = Checkbutton(self, text="EPassport", variable=self.epCheck, command=self.refresh)
        ep.pack(side=LEFT)

        self.smCheck = BooleanVar()
        self.smCheck.set(configManager().getOption('Logs','sm'))
        sm = Checkbutton(self, text="Secure Messaging", variable=self.smCheck, command=self.refresh)
        sm.pack(side=LEFT, padx=10)

        self.isoCheck = BooleanVar()
        self.isoCheck.set(configManager().getOption('Logs','apdu'))
        iso = Checkbutton(self, text="ISO7816", variable=self.isoCheck, command=self.refresh)
        iso.pack(side=LEFT)

        self.bacCheck = IntVar()
        self.bacCheck.set(configManager().getOption('Logs','bac'))
        bac = Checkbutton(self, text="BAC", variable=self.bacCheck, command=self.refresh)
        bac.pack(side=LEFT, padx=10)

        saveButton = Button(self, text="Save...", command=self.save)
        saveButton.pack(side=RIGHT, padx=5, pady=3)

        self.createLog()

    def refresh(self):
        configManager().setOption('Logs','api', self.epCheck.get())
        configManager().setOption('Logs','sm', self.smCheck.get())
        configManager().setOption('Logs','apdu', self.isoCheck.get())
        configManager().setOption('Logs','bac', self.bacCheck.get())

        self.createLog()


    def createLog(self):
        l = list()
        if self.epCheck.get(): l.append("EPassport")
        if self.smCheck.get(): l.append("SM")
        if self.isoCheck.get(): l.append("ISO7816")
        if self.bacCheck.get(): l.append("BAC")

        with open(LOG,'r') as f:
            lines = f.readlines()

        textlog = ""
        for line in lines:
            for category in l:
                if line[:len(category)] == category:
                    textlog += line

        self.logFrame.updateText(textlog)


    def save(self):
        formats = [('Raw text','*.txt')]

        fileName = asksaveasfilename(parent=self,filetypes=formats ,title="Save as...")
        if len(fileName) > 0:
            try:
                file = open(str(fileName), 'w')
                file.write(self.logFrame.text.get(1.0, END))
                tkMessageBox.showinfo("Log saved", "Log saved as: {}".format(str(fileName)))
            except Exception, msg:
		# BUG, allow user to save in .xXx or put only .txt in error message
                tkMessageBox.showerror("Save error", str(msg))
            finally:
                file.close()


class ProgressBar(Frame):
    def __init__(self, master=None, orientation="horizontal",
                 min=0, max=100, width=300, height=18,
                 doLabel=1, appearance="sunken",
                 fillColor="blue", background="gray",
                 labelColor="yellow", labelFont="Verdana",
                 labelText="reading", labelFormat="%d%%",
                 value=0, bd=2):
        Frame.__init__(self, master, relief=appearance, bd=bd)
        # preserve various values
        self.master=master
        self.orientation=orientation
        self.min=min
        self.max=max
        self.width=width
        self.height=height
        self.doLabel=doLabel
        self.fillColor=fillColor
        self.labelFont= labelFont
        self.labelColor=labelColor
        self.background=background
        self.labelText=labelText
        self.labelFormat=labelFormat
        self.value=value
        #self.frame=Frame(master, relief=appearance, bd=bd)
        self.canvas=Canvas(self, height=height, width=width, bd=0, highlightthickness=0, background=background)
        self.scale=self.canvas.create_rectangle(0, 0, width, height, fill=fillColor)
        self.label=self.canvas.create_text(self.canvas.winfo_reqwidth()/ 2,
                                           height / 2, text=labelText,
                                           anchor="c", fill=labelColor,
                                           font=self.labelFont)
        self.update()
        self.canvas.pack(side=TOP, expand=False)

#        self.frame.pack(side=TOP, fill=X, expand=False)

    def updateProgress(self, newValue, newMax=None):
        if newMax:
            self.max = newMax
        self.value = newValue
        self.update()

    def update(self):
        # Trim the values to be between min and max
        value=self.value
        if value > self.max:
            value = self.max
        if value < self.min:
            value = self.min
        # Adjust the rectangle
        if self.orientation == "horizontal":
            self.canvas.coords(self.scale, 0, 0,
              float(value) / self.max * self.width, self.height)
        else:
            self.canvas.coords(self.scale, 0,
                               self.height - (float(value) / self.max*self.height),
                               self.width, self.height)
        # Now update the colors
        self.canvas.itemconfig(self.scale, fill=self.fillColor)
        self.canvas.itemconfig(self.label, fill=self.labelColor)
        # And update the label
        if self.doLabel:
            if value:
                if value >= 0:
                    pvalue = int((float(value) / float(self.max)) * 100.0)
                else:
                    pvalue = 0
                self.canvas.itemconfig(self.label, text=self.labelFormat % pvalue)
            else:
                self.canvas.itemconfig(self.label, text='')
        else:
            self.canvas.itemconfig(self.label, text=self.labelFormat % self.labelText)
        self.canvas.update_idletasks()


class WrongMRZ(Exception):
    def __init__(self, *params):
        Exception.__init__(self, *params)

class ReadingDialog(threading.Thread, Toplevel):

    def __init__(self, master, doc9303):
        threading.Thread.__init__(self)
        Toplevel.__init__(self, master)
        self.log = datagroup.Events()
        self.queue = Queue.Queue()
        self.master = master

        self.doc = doc9303
        self.doc._dgReader.processed.register(self.DGcallBack)
        self.ep = None

        self.__dgList = []
        self.withdraw()
        self.resizable(False, False)

        self.title("Reading...")
        self.transient(master)
        self.grab_set()
        #self.transient = self.master
        self.protocol("WM_DELETE_WINDOW", self.stopReading)


        # GRAPHIC COMPONENTS
        self.lPassport=Label(self, text="Passport processing")
        self.lPassport.grid(column=1, columnspan=3, padx=5)

        self.pbPassport = ProgressBar(self, value=1)
        self.pbPassport.grid(column=1, columnspan=3, padx=5, pady=5)

        self.svDG = StringVar()
        self.lDG=Label(self,textvariable=self.svDG)
        self.lDG.grid(column=1, columnspan=3, padx=5)

        self.pbDG = ProgressBar(self)
        self.pbDG.grid(column=1, columnspan=3, padx=5, pady=5)

        self.bcancel=Button(self, text="Cancel", command=self.stopReading)
        self.bcancel.grid(column=2, padx=5, pady=5)

        #CallBack
        self.e = threading.Event()
        self.read = datagroup.Events()

        self.stop = False
        self.destoyed = False
        self.periodicCall()

    def processIncoming(self):
        while self.queue.qsize() and not self.destoyed:
            try:
                a = self.queue.get(0)
                if not a: continue
                msg, widget, cpt = a
                if widget == 'passport':
                    self.pbPassport.updateProgress(cpt)
                elif widget == 'dg':
                    self.pbDG.updateProgress(cpt)
                elif widget == 'svdg':
                    self.svDG.set(cpt)
                if msg == 'Quit':
                    self.stopReading()
                elif msg == 'Reset':
                    self.stopReading()
                    self.master.clean()
                    self.doc = None
                    self.ep = None
                elif msg:
                    self.read.log(msg)
                if self.stop:
                    self.destroy()
                    self.destoyed = True
            except Queue.Empty, msg:
                if DEBUG: 'Queue Error:', msg
                pass


    def show(self):
        self.deiconify()
#        self.startReading()
        self.thread = threading.Thread(target=self.startReading)
        self.thread.start()

    def showSafe(self):
        self.deiconify()
        self.startReading()
#        self.thread = threading.Thread(target=self.startReading)
#        self.thread.start()

    def rstConnection(self):
        try:
            self.doc.getCommunicationLayer().rstConnection()
            self.doc.doBasicAccessControl()
        except Exception, msg:
            tkMessageBox.showerror("Error while resetting", "{}\nPlease try to read the passport again.".format(errorhandler.getID(msg)))

    def startReading(self):

        try:
            cpt=0
            start = time.time()

            try:
                self.dgList = self._reorder(self.doc["Common"]["5C"])
                self.queue.put((("BAC", True), 'None', 0))
            except epassport.bac.BACException, msg:
                raise WrongMRZ("Please check you wrote the correct MRZ.".format(type(msg), msg))
            except Exception, msg:
                raise Exception(msg)

            c = len(self.dgList)
            if configManager().getOption('Security','pa'):
                c += 1
            if configManager().getOption('Security','aa'):
                c += 1

            self.pbPassport.updateProgress(0, c)


            dgValidList = list()
            self.ep = dict()
            for item in self.dgList:
                cpt+=1
                msg = "Reading " + toDG(str(item))
                self.queue.put((None, 'svdg', msg))

                try:
                    dg = self.doc[item]
                    dgValidList.append(item)
                    self.ep[item] = dg
                except BACException:
                    self.queue.put((("EAC", item), 'None', 0))
                    self.rstConnection()
                    dg = ''

                self.queue.put(((toTAG(item), dg), 'passport', cpt))

            #AA
            #True: The AA is ok
            #Flase : The AA is not ok
            #None: The AA is not supported
            if configManager().getOption('Security','aa'):
                if self.doc.has_key(toTAG("DG15")):

                    self.queue.put((None, 'svdg', "Active Authentication"))
                    self.queue.put((None, 'dg', 0))
                    try:
                        res = self.doc.doActiveAuthentication()
                    except epassport.openssl.OpenSSLException, msg:
                        res = "NO_OPENSSL"
                    except epassport.activeauthentication.ActiveAuthenticationException:
                        res = "NO_DG_15"
                else:
                    res = "NO_DG_15"

                self.queue.put((("AA", res), 'dg', 100))
                cpt += 1
                self.queue.put((None, 'passport', cpt))

            # PASSIVE AUTHENTICATION
            if configManager().getOption('Security','pa'):
                self.queue.put((None, 'svdg', "Passive Authentication: Certificate Verification"))
                self.queue.put((None, 'dg', 0))

                try:
                    if configManager().getOption('Options','certificate'):
                        self.doc.setCSCADirectory(configManager().getOption('Options','certificate'), False)
                    certif = self.doc.doVerifySODCertificate()
                    if not configManager().getOption('Options','certificate'):
                        certif = "CA_NOT_SET"
                except epassport.openssl.OpenSSLException, msg:
                    certif = "OPENSSL_ERROR"
                except epassport.passiveauthentication.PassiveAuthenticationException, msg:
                    certif = "PA_ERROR"
                except Exception, msg:
                    tkMessageBox.showinfo("DEBUG", "{}.\n{}".format(str(msg), type(msg)))

                self.queue.put((None, 'svdg', "Passive Authentication: Data Group Integrity Verification"))
                self.queue.put((None, 'dg', 50))

                try:
                    dgs = []
                    for dg in dgValidList:
                        dgs.append(self.doc[dg])
                    dgsIntegrity = self.doc.doVerifyDGIntegrity(dgs)
                except epassport.openssl.OpenSSLException, msg:
                    dgsIntegrity = {}
                    for dg in self.dgList:
                        dgsIntegrity[toDG(dg)] = "NO_OPENSSL"

                self.queue.put((("PA", (certif, dgsIntegrity)), 'dg', 100))

                cpt += 1
                self.queue.put((None, 'passport', cpt))

            self.master.footer.set("Reading Time : " + str(time.time() - start)[:5] + " sec ")
            self.queue.put(('Quit', 'dg', 100))

        except WrongMRZ, msg:
            self.queue.put(('Reset', None, 0))
            time.sleep(0.3)
            tkMessageBox.showinfo("Wrong MRZ", str(msg))
        except epassport.bac.BACException, msg:
            self.queue.put(('Reset', None, 0))
            time.sleep(0.3)
            tkMessageBox.showinfo("BAC error", "{}\nPlease try to read the passport again.".format(errorhandler.getID(msg)))
        except Exception, msg:
            self.queue.put(('Reset', None, 0))
            time.sleep(0.3)
            tkMessageBox.showinfo("Unknown error", "{}\nPlease try to read the passport again.".format(errorhandler.getID(msg)))


    def periodicCall(self):
        self.processIncoming()
        if not self.destoyed:
            self.after(100, self.periodicCall)

    def stopReading(self):
        self.doc.stopReading()
        self.stop = True

    def DGcallBack(self, value):
        self.queue.put((None, "dg", value))

    def _getDGList(self):
        return self.__dgList

    def _setDGList(self, value):
        self.__dgList = value

    def _reorder(self, list):
        """ Use to read bigger files at the end

            @param list: Datagroup presence list
            @type list: list
            @return: list ordered with bigger files at the end
        """
        for item in ["67", "75"]:
            try:
                list.remove(item)
                list.append(item)
            except ValueError, msg:
                pass
        return list

    def logFingerprint(self, fingerprint):
        def recTraversal(dic, level):
            for key in dic:
                if type(dic[key]) == type({}):
                    recTraversal(dic[key], level+1)
                else:
                    self.log.log(" > "*level + key + ": " + str(dic[key]))

        recTraversal(fingerprint, 0)

    def log(self, data):
        try:
            log = open(LOG, 'a')
            log.write(data+'\n')
        except Exception, msg:
            pass
        finally:
            log.close()

    dgList = property(_getDGList, _setDGList)



class ScrollFrame(Frame):
    def __init__(self, master, txt='', height=24):
        Frame.__init__(self, master)
        scrollbar = Scrollbar(self)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.text = Text(self, yscrollcommand=scrollbar.set, height=height)
        self.text.insert(END, txt)
        self.text.config(state=DISABLED)
        self.text.pack(side=TOP, fill=BOTH, expand=True)
        scrollbar.config(command=self.text.yview)

    def updateText(self, txt, disable=True):
        self.text.config(state=NORMAL)
        self.text.delete("1.0", END)
        self.text.insert(END, txt)
        if disable:
            self.text.config(state=DISABLED)
        self.update()


######
# HELP
######

class InfoBoxWindows(Toplevel):
    def __init__(self, master, title_dialog, text_dialog):
        Toplevel.__init__(self, master)
        self.title("Help: {0}".format(title_dialog))
        self.transient(master)
        self.resizable(False,False)

        helpFrame = Frame(self, relief=RAISED, borderwidth=0)
        helpFrame.pack(fill=BOTH, expand=1)

        helpLabel = Label(helpFrame, text=text_dialog, justify=LEFT)
        helpLabel.pack(padx=5, pady=5)

        closeButton = Button(helpFrame, text="Close", command=self.destroy)
        closeButton.pack(padx=5, pady=5)


class Tooltip(Toplevel):
	def __init__(self, parent=None, tip='',time=500):
		Toplevel.__init__(self, parent, bd=1, bg='black')
		self.time = time
		self.parent = parent
		self.withdraw()
		self.overrideredirect(1)
		self.transient()
		l = Label(self, text=tip, bg="#FFFECD", justify='left')
		l.update_idletasks()
		l.pack()
		l.update_idletasks()
		self.tipwidth = l.winfo_width()
		self.tipheight = l.winfo_height()
		self.parent.bind('<Enter>', self.delay)
		self.parent.bind('<Button-1>', self.clear)
		self.parent.bind('<Leave>', self.clear)
		
	def delay(self,event):
		self.action = self.parent.after(self.time, self.show)
		
	def show(self):
		self.update_idletasks()
		posX = self.parent.winfo_rootx()+self.parent.winfo_width()-10
		posY = self.parent.winfo_rooty()+self.parent.winfo_height()-10
		if posX + self.tipwidth > self.winfo_screenwidth():
			posX = posX-self.winfo_width()-self.tipwidth
		if posY + self.tipheight > self.winfo_screenheight():
			posY = posY-self.winfo_height()-self.tipheight
		self.geometry('+%d+%d'%(posX,posY))
		self.deiconify()
		
	def clear(self, event):
		self.withdraw()
		self.parent.after_cancel(self.action)


class AdditionalData(Toplevel):
    def __init__(self, master, doc):
        Toplevel.__init__(self, master)
        self.title("Additional Data")
        self.transient(master)
        self.doc = doc



        self.files = Listbox(self, width=12)
        self.files.pack(side=LEFT, fill=Y)

        scrollbar = Scrollbar(self)
        scrollbar.pack(side=LEFT, fill=BOTH)
        scrollbar.config(command=self.files.yview)

        self.files['yscrollcommand'] = scrollbar.set

        self.data = DataGroupGridList(self, None, ['Tag', 'Value'], 10, None, None)

        for item in doc.keys():
            self.files.insert(END, toDG(item))

        self.files.bind('<<ListboxSelect>>', self.onSelectDG)

        self.data.load(self.doc[toTAG("DG1")])

    def onSelectDG(self, event=None):
        self.data.load(self.doc[toTAG(self.files.get(event.widget.curselection()))])

    def clickOk(self, event=None):
        self.destroy()


class AdditionalDialog:

    # close the window and quit
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def __init__(self, dgs):

        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        self.window.set_title("Additional Data")

        self.window.set_size_request(500, 400)

        self.window.connect("delete_event", self.delete_event)

        self.doc = dgs
        
        # create a TreeStore with one string column to use as the model
        self.treestore = gtk.TreeStore(str)

        #for item in self.doc.keys():
        #print type(self.doc.keys), self.doc.keys
        orderedlist = list()
        for val in self.doc.keys():
            orderedlist.append(toOrder(val))
        orderedlist.sort()
        for order in orderedlist:
            item = toTAG(order)
            root = self.treestore.append(None, [toDG(item)])
            for value in self.doc[item]:
                branch = self.treestore.append(root, [str(value)])
                # leave => nouvelle position
                if type(self.doc[item][value]) == str:
                    leave = self.treestore.append(branch, [self.doc[item][value]])
                elif type(self.doc[item][value]) == list:
                    for data in self.doc[item][value]:
                        self.treestore.append(branch, [data])
                elif type(self.doc[item][value]) == type(datagroup.DataGroup()): # the picure (binary)
                    self.treestore.append(branch, [str(self.doc[item][value])])

        # create the TreeView using treestore
        self.treeview = gtk.TreeView(self.treestore)

        # create the TreeViewColumn to display the data
        self.tvcolumn = gtk.TreeViewColumn('Data groups')

        # add tvcolumn to treeview
        self.treeview.append_column(self.tvcolumn)

        # create a CellRendererText to render the data
        self.cell = gtk.CellRendererText()

        # add the cell to the tvcolumn and allow it to expand
        self.tvcolumn.pack_start(self.cell, True)

        # set the cell "text" attribute to column 0 - retrieve text
        # from that column in treestore
        self.tvcolumn.add_attribute(self.cell, 'text', 0)

        # make it searchable
        self.treeview.set_search_column(0)

        # Allow sorting on the column
        self.tvcolumn.set_sort_column_id(1)

        # Allow drag and drop reordering of rows
        self.treeview.set_reorderable(True)

        self.scollwin = gtk.ScrolledWindow()
        self.scollwin.add_with_viewport(self.treeview)

        self.window.add(self.scollwin)

        self.window.show_all()



class FingerprintProcess(threading.Thread, Toplevel):

    def __init__(self, master, doc9303):
        threading.Thread.__init__(self)
        Toplevel.__init__(self, master)
        self.queue = Queue.Queue()

        self.doc = doc9303
        self.master = master

        self.resizable(False, False)

        self.title("Generating the report...")
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.stopReading)


        # GRAPHIC COMPONENTS
        self.svDG = StringVar()
        self.lfp = Label(self,textvariable=self.svDG)
        self.lfp.pack(side=TOP, fill=X, padx=5)

        self.pbfp = ProgressBar(self)
        self.pbfp.pack(side=TOP, fill=X, padx=5, pady=5)

        #self.txt = ""

        self.stop = False
        self.destoyed = False
        self.periodicCall()

    def processIncoming(self):
        while self.queue.qsize() and not self.destoyed:
            try:
                a = self.queue.get(0)
                if not a: continue
                msg, widget, cpt = a
                if widget == 'fp':
                    self.pbfp.updateProgress(cpt)
                elif widget == 'slfp':
                    self.svDG.set(cpt)
                if msg == 'Quit':
                    self.stopReading()
                elif msg == 'Reset':
                    self.stopReading()
                    self.master.clear()
                    self.doc = None
                if self.stop:
                    self.destroy()
                    self.destoyed = True
            except Queue.Empty, msg:
                if DEBUG: 'Queue Error:', msg
                pass

    def showSafe(self):
        self.thread = threading.Thread(target=self.startReading)
        self.thread.start()

    def startReading(self):
        self.queue.put((None, 'slfp', "Initializing"))
        self.queue.put((None, 'fp', 0))
        try:
            certfir = None
            if configManager().getOption('Options','certificate'):
                certfir = configManager().getOption('Options','certificate')
            fp = fingerPrint.FingerPrint(self.doc, certfir, self.queue)
            data = fp.analyse()
            name, mrz = self.master.extractOwnerInfo(self.doc["DG1"])
            self.master.addToHistory(name, mrz)
            self.queue.put(('Quit', 'fp', 100))
            FingerPrintDialog(self.master, data)
        except Exception, msg:
            self.queue.put(('Quit', 'fp', 100))
            time.sleep(0.3)
            tkMessageBox.showinfo("Report error", "{}\nPlease try to run the report again.".format(errorhandler.getID(msg)))



    def periodicCall(self):
        self.processIncoming()
        if not self.destoyed:
            self.after(100, self.periodicCall)

    def stopReading(self):
        self.doc.stopReading()
        self.stop = True


class FingerPrintDialog(Toplevel):

    def __init__(self, master, data):
        self.txt = ""
        self.analyse = data
        self.buildText()

        self.buttonText = StringVar()
        self.buttonText.set("Anonymize report")

        Toplevel.__init__(self, master)
        self.title("Report")
        self.transient(master)

        self.log = ScrollFrame(self, self.txt)
        self.log.pack(side=TOP, fill=BOTH, expand=True)

        saveButton = Button(self, width=10, text="Save...", command=self.save)
        saveButton.pack(side=LEFT, ipadx=10)

        sendButton = Button(self, width=10, textvariable=self.buttonText, command=self.anonymize)
        sendButton.pack(side=LEFT, ipadx=10)

        self.withdraw()
        self.deiconify()
        self.update()

    def save(self):
        formats = [('Raw text','*.txt'),('PDF','*.pdf')]

        fileName = asksaveasfilename(parent=self,filetypes=formats ,title="Save current frame as...")
        if fileName[-4:] == ".txt":
            try:
                with open(str(fileName), 'w') as file:
                    file.write(self.txt)
                    tkMessageBox.showinfo("File saved", "File saved as "+fileName)
            except Exception, msg:
                tkMessageBox.showerror("Save error", str(msg))

        elif fileName[-4:] == ".pdf":
            inOut.toPDF(self.analyse, fileName)
            tkMessageBox.showinfo("File saved", "File saved as "+fileName)

    def anonymize(self):
        self.txt = ""

        if self.buttonText.get() == "Anonymize report":
            self.buildText(anonymize=True)
            self.buttonText.set("Reset")
            self.log.updateText(self.txt, False)


        elif self.buttonText.get() == "Reset":
            self.buildText()
            self.buttonText.set("Anonymize report")
            self.log.updateText(self.txt)

    def buildText(self, anonymize=False):
        data = self.analyse
        if anonymize:
            self.txt += "Please send (copy all) this anonymized report to: " + CONTACT + "\n"
            self.txt += "with the subject: ePassport Viewer Report\n"
            self.txt += "\n"
            self.txt += "Country: " + data["EP"]['DG1']['5F28'] + "\n"
            self.txt += "Issue Date: " + data["EP"]['DG12']['5F26'][:4] + "\n"
            self.txt += "\n"
        self.txt += "====================\n"
        self.txt += "   IDENTIFICATION   \n"
        self.txt += "====================\n"
        self.txt += "\n"
        if not anonymize:
            self.txt += "Holder's name: " + data["EP"]["DG1"]["5F5B"].replace("<", " ") + "\n"
            self.txt += "\n"
        self.txt += "Unique ID: " + data["UID"] + "\n"
        self.txt += "Answer-To-Reset: " + data["ATR"] + "\n"
        self.txt += "\n"
        self.txt += "\n"
        self.txt += "==========================\n"
        self.txt += "   Basic Access Control   \n"
        self.txt += "==========================\n"
        self.txt += "\n"
        self.txt += "Basic Access Control: " + data["bac"] + "\n"
        self.txt += "Reading time: " + str(data["ReadingTime"]) + "\n"
        self.txt += "\n"
        self.txt += "Data Groups size: "
        if type(data["DGs"]) == type([]):
            self.txt += "\n"
            for key, value in data["DGs"]:
                self.txt += "   - " + str(key) + ": " + str(value) + " octets\n"
        else:
            self.txt += data["DGs"] + "\n"
        self.txt += "\n"
        if not anonymize:
            for dg in data["EP"]:
                self.txt += dg + "\n"
                self.txt += "====\n"
                if dg == "DG15":
                    self.txt += "See section Active Authentication\n"
                self.browseDGs(data["EP"][dg].parse())
                self.txt += "\n"
        self.txt += "\n"
        self.txt += "============================\n"
        self.txt += "   Passive Authentication   \n"
        self.txt += "============================\n"
        self.txt += "\n"
        self.txt += "SOD verified by CSCA: " + str(data["verifySOD"]) + "\n"
        self.txt += "\n"
        self.txt += "DG integrity\n"
        self.txt += "============\n"
        for dgi in data["Integrity"]:
            self.txt += dgi + ": "
            if data["Integrity"][dgi] == True:
                self.txt += "Verified"
            elif data["Integrity"][dgi] == False:
                self.txt += "Not verified"
            elif data["Integrity"][dgi] == None:
                self.txt += "No hash present in SOD for this EF"
            else:
                self.txt += "N/A"
            self.txt += "\n"
        self.txt += "\n"
        if not anonymize:
            self.txt += "DG hashes\n"
            self.txt += "=========\n"
            for dgi in data["Hashes"]:
                self.txt += dgi + ": " + binToHexRep(data["Hashes"][dgi]) + "\n"
            self.txt += "\n"
        if anonymize:
            self.txt += "SOD\n"
            self.txt += "===\n"
            self.txt += "\n"
            self.txt += "Hash algorithm: " + data["Algo"] + "\n"
            self.txt += "\n"
        else:
            self.txt += "SOD\n"
            self.txt += "===\n"
            self.txt += "\n"
            self.txt += data["SOD"] + "\n"
            self.txt += "\n"
        self.txt += "CERTIFICATES\n"
        self.txt += "============\n"
        self.txt += "\n"
        self.txt += "Certificate Serial Number:" + data["certSerialNumber"] + "\n"
        self.txt += "Certificate Fingerprint:" + data["certFingerPrint"] + "\n"
        self.txt += "\n"
        self.txt += "Document Signer\n"
        self.txt += "===============\n"
        self.txt += data["DSCertificate"] + "\n"
        self.txt += "\n"
        self.txt += "\n"
        self.txt += "===========================\n"
        self.txt += "   Active Authentication   \n"
        self.txt += "===========================\n"
        self.txt += "\n"
        self.txt += "Active Authentication " + data["activeAuth"] + "\n"
        self.txt += "\n"
        if not anonymize:
            self.txt += "Public Key\n"
            self.txt += "==========\n"
            self.txt += data["pubKey"] + "\n"
            self.txt += "\n"
        self.txt += "\n"
        self.txt += "=============================\n"
        self.txt += "   Extended Access Control   \n"
        self.txt += "=============================\n"
        self.txt += "\n"
        self.txt += "EAC has not been implemented yet.\n"
        self.txt += "Here is of DG that the reader cannot access:\n"
        for fdg in data["failedToRead"]:
            self.txt += "  - " + fdg + "\n"
        if not data["failedToRead"]:
            self.txt += "  List empty: No EAC implemented in passport\n"
        self.txt += "\n"
        self.txt += "\n"
        self.txt += "============================\n"
        self.txt += "   Security investigation   \n"
        self.txt += "============================\n"
        self.txt += "\n"
        self.txt += "Security measures\n"
        self.txt += "=================\n"
        self.txt += "\n"
        self.txt += "Delay security measure after a wrong BAC: " + str(data["delaySecurity"]) + "\n"
        self.txt += "Block the communication after a wrong BAC: " + str(data["blockAfterFail"]) + "\n"
        self.txt += "\n"
        self.txt += "Potential vulnerabilities\n"
        self.txt += "=========================\n"
        self.txt += "\n"
        (vuln, ans) = data["activeAuthWithoutBac"]
        self.txt += "Active Authentication before BAC: " + str(vuln) + "\n"
        if vuln: self.txt += "  * Vulnerable to AA Traceability\n"
        (vuln, comment) = data["macTraceability"]
        self.txt += "Vulnerable to MAC traceability: " + str(vuln) + "\n"
        self.txt += "  " + comment + "\n"
        (vuln, error) = data["getChallengeNull"]
        self.txt += "Passport answer to a GET CHALLENGE with the Le set to '01': " + str(vuln) + "\n"
        if vuln:
            self.txt += "  * Vulnerable to lookup brute force\n"
        self.txt += "\n"
        self.txt += "Select 00 response: " + data["selectNull"] + "\n"
        self.txt += "\n"
        self.txt += "Error Fingerprinting\n"
        self.txt += "====================\n"
        self.txt += "\n"
        for ins in data["Errors"]:
            self.txt += 'APDU "00" "' + ins + '" "00" "00" "" "" "00": ' + data["Errors"][ins] + "\n"




    def browseDGs(self, data, level=0):
        dgtypes = [DataGroup1, DataGroup2, DataGroup3, DataGroup4, DataGroup5,
                   DataGroup6, DataGroup7, DataGroup8, DataGroup9, DataGroup10,
                   DataGroup11, DataGroup12, DataGroup13, DataGroup14, DataGroup15,
                   DataGroup16, DataGroup, Com, SOD]
        i = level
        if type(data) == type(dict()) or type(data) in dgtypes:
            for x in data:
                self.txt += self.truncate(x, i*"  ")
                if type(data[x]) == type(dict()) or type(data[x]) == type(list()) or type(data[x]) in dgtypes:
                    self.browseDGs(data[x], i+1)
                else:
                    self.txt += self.truncate(data[x], (i+1)*"  ")

        elif type(data) == type(list()):
            for x in data:
                if type(x) == type(dict()) or type(x) == type(list()) or type(x) in dgtypes:
                    self.browseDGs(x, i+1)
                else:
                    self.txt += self.truncate(x, (i+1)*" ")

    def truncate(self, data, sep="  ", length=200):
        try:
            return sep + (str(data)[:length].encode("utf-8") + '..') if len(str(data).encode("utf-8")) > length else sep + str(data).encode("utf-8") + "\n"
        except Exception:
            return sep + "UNPRINTABLE BINARY VALUE\n"





