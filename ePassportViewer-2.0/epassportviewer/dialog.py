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
import thread
import threading
import tkFont
import Image, ImageTk
import Queue
import time
import re
from tkFileDialog import askdirectory, askopenfilename

from epassportviewer.const import *
from epassportviewer.util import forge
from epassportviewer.util.image import ImageFactory
from epassportviewer.util.components import DataGroupGridList
from epassportviewer.util.configManager import configManager

from pypassport import epassport
from pypassport import fingerPrint
from pypassport.doc9303 import datagroup
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
        
        waitFrame = Frame(self, borderwidth=1, relief=GROOVE)
        waitFrame.pack(fill=BOTH, expand=1)
        
        waitLabel = Label(waitFrame, text="Please wait while the ePassport is generated")
        waitLabel.grid(row=0, column=0, padx=10, pady=10)
        
    def closeDialog(self):
        self.destroy()
            
            
            
            

class About(Toplevel):
    
    VERSIONTEXT = "Version " + VERSION
    
    DESCRIPTION = """ePassport Viewer is a biometric passport viewer.\n\
This application is based on the pyPassport Project\n\
and illustrate how to use it.\n\
Features include viewing data, fingerprinting and\n\
performing e-Passport security mechanisms."""    
    
    AUTHORS = "\nJean Francois HOUZARD (jhouzard@gmail.com)\n\
 Olivier ROGER (olivier.roger@gmail.com)\n"
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
        
        file = open(LOG,'r')
        self.txt = file.read()
        file.close()
         
        log = ScrollFrame(self, self.txt)
        log.pack(side=TOP, fill=BOTH, expand=True)

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
        
class FingerPrintDialog(Toplevel):
    
    def __init__(self, master, data):
        Toplevel.__init__(self, master)
        self.title("Fingerprint")
        self.transient(master)
        self.grab_set()
        
        self.txt = ""
        self.txt += "Unique ID (random): " + data["UID"] + "\n"
        self.txt += "Answer-To-Reset: " + data["ATR"] + "\n"
        self.txt += "Generation: " + str(data["generation"]) + "\n"
        self.txt += "Reading time: " + str(data["ReadingTime"]) + "\n"
        self.txt += "Data Groups size: "
        if type(data["DGs"]) == type([]):
            self.txt += "\n"
            for key, value in data["DGs"]:
                self.txt += "   - " + str(key) + ": " + str(value) + "\n"
        else:
            self.txt += data["DGs"] + "\n"
        self.txt += "\n"
        self.txt += "\n"
        self.txt += "SECURITY\n"
        self.txt += "\n"
        self.txt += "   Basic Access Control: " + data["bac"] + "\n"
        self.txt += "   Active Authentication: " + data["activeAuth"] + "\n"
        self.txt += "   Active Authentication without BAC: " + str(data["activeAuthWithoutBac"]) + "\n"
        if data["activeAuthWithoutBac"]: self.txt += "    * Vulnerable to AA traceability\n"
        self.txt += "   Diffirent repsonse time for wrong message or MAC: " + str(data["macTraceability"]) + "\n"
        if data["macTraceability"]: 
            self.txt += "    * Vulnerable to MAC traceability\n"
            self.txt += "      Note: If french passport, this might be a false positive due to the anti brute-force \n"
        self.txt += "\n"
        self.txt += "\n"
        self.txt += "CERTIFICATES/SIGNATURES\n"
        self.txt += "\n"
        self.txt += "Certificate Serial Number: " + data["certSerialNumber"] + "\n"
        self.txt += "Certificate Fingerprint: " + data["certFingerPrint"] + "\n"
        self.txt += "\n"
        self.txt += "Document Signer " + data["DSCertificate"] + "\n"
        self.txt += "\n"
        self.txt += data["pubKey"] + "\n"
        
        log = ScrollFrame(self, self.txt)
        log.pack(side=TOP, fill=BOTH, expand=True)
        
        saveButton = Button(self, text="Save")
        saveButton.pack(side=RIGHT, ipadx=10)
        saveButton.bind("<Button-1>", self.save)
        
        okButton = Button(self, text="OK")
        okButton.pack(side=RIGHT, ipadx=10)
        okButton.bind("<Button-1>", self.clickOK)

    def save(self, event):
        from tkFileDialog import asksaveasfilename
        formats = [
            ('Text','*.txt'),
            ]
        
        fileName = asksaveasfilename(parent=self,filetypes=formats ,title="Save as...")
        if len(fileName) > 0:
            try:
                file = open(str(fileName), 'w')
                file.write(self.txt)
            except Exception, msg:
                tkMessageBox.showerror("Save error", str(msg))
            finally:
                file.close()

    def clickOK(self, event):
        self.destroy()

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
        
class ReadingDialog(threading.Thread, Toplevel):       
    
    def __init__(self, master, doc9303, fingerprint):
        threading.Thread.__init__(self)
        Toplevel.__init__(self, master)
        self.log = datagroup.Events()
        self.fingerprint = fingerprint
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
#        self.grab_set()
        self.transient = self.master
        self.protocol("WM_DELETE_WINDOW", self.stopReading)
        
        self.lPassport=Label(self,text="Passport processing")
        self.pbPassport = ProgressBar(self, value=1)
        self.svDG = StringVar()
        self.lDG=Label(self,textvariable=self.svDG)
        self.pbDG = ProgressBar(self)
        self.svCancel = StringVar()
        self.svCancel.set("Cancel")
        self.bcancel=Button(self,textvariable=self.svCancel,command=self.stopReading)
        
        self.lPassport.grid(column=1, columnspan=3, padx=5)
        self.pbPassport.grid(column=1, columnspan=3, padx=5, pady=5)
        self.lDG.grid(column=1, columnspan=3, padx=5)
        self.pbDG.grid(column=1, columnspan=3, padx=5, pady=5)
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
                    self.stop = True
                elif msg == 'Clear':
                    self.master.clear()
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
            tkMessageBox.showerror("Error", msg)
        
    def startReading(self):
        
        try:
            cpt=0
            start = time.time()
            
            try:
                self.dgList = self._reorder(self.doc["Common"]["5C"])
            except BACException:
                tkMessageBox.showinfo("Wrong MRZ", "Please check you wrote the correct MRZ")
            except Exception, msg:
                tkMessageBox.showinfo("Error: {0}".format(type(msg)), "{0}".format(msg))
            
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
                    tkMessageBox.showinfo("EAC required", "{0} can't be read".format(tagLDSToName[item]))
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
            # PA is not possible if one of the DG cannot be read
            # Therefore no PA is executed if at least one dg failed
            if configManager().getOption('Security','pa'):
                self.queue.put((None, 'svdg', "Passive Authentication: Certificate Verification"))
                self.queue.put((None, 'dg', 0))
                
                try:
                    certif = self.doc.doVerifySODCertificate()
                except epassport.openssl.OpenSSLException, msg:
                    certif = "NO_OPENSSL"
                except epassport.passiveauthentication.PassiveAuthenticationException, msg:
                    certif = "NO_OPENSSL"
                
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
                
        except epassport.bac.BACException, msg:
            self.queue.put(('Clear', None, 0))
            raise Exception(msg)
#        except epassport.iso7816.Iso7816Exception, msg: 
#            print 'error', msg
        except Exception, msg:
            self.queue.put(('Clear', None, 0))
            tkMessageBox.showerror("Unknown Error", msg)
        finally:
            self.queue.put(('Quit', 'dg', 100))
        
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
    def __init__(self, master, txt, height=24):
        Frame.__init__(self, master)
        scrollbar = Scrollbar(self)
        scrollbar.pack(side=RIGHT, fill=Y)
        text = Text(self, yscrollcommand=scrollbar.set, height=height)
        text.insert(END, txt)
        text.pack(side=TOP, fill=BOTH, expand=True)
        scrollbar.config(command=text.yview) 

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
    


