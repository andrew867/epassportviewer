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
import time
import types
import os
import PIL

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from string import replace
from xml.dom.minidom import Document, parse

from pypassport.hexfunctions import *
from pypassport.doc9303.converter import toDG, toOrder
from pypassport.doc9303.tagconverter import tagToName
from pypassport.jp2converter import jp2ConverterException
from epassportviewer.util.image import writeImageToDisk
from epassportviewer.util.helper import getItem, getItemByTag, getItemRaw

#TODO : Problem when loading signature !
#def fromXML(filename):
#    def rec(node, format=""):
#        isList = False
#        dict = {}
#        list = []
#        for item in node.childNodes:
#            if item.nodeType == item.ELEMENT_NODE:
#                if item.nodeName == "Item": isList = True
#                if isList:
#                    list.append(rec(item))
#                else:
#                    dict[str(item.getAttribute("Value"))] = rec(item,item.getAttribute("Format"))
#            elif item.nodeType == item.TEXT_NODE:
#                if format == "HexRep":
#                    return hexRepToList(str(item.data))
#                return binToHexList(str(item.data))
#            else:
#                #TODO: (XML) Handle Error
##                print ">>", item.nodeType
#                return ""
#        if isList: return list
#        return dict
#                        
#    data = {} #doc9303(None,None)
#    doc = parse(filename)
#    files = doc.getElementsByTagName("Files")
#    for file in files[0].childNodes:
#        data[str(file.getAttribute("Value"))] = rec(file)     
#    return data

#TODO: Return True on success and test it ?

def toXML(doc,filename):
    """ Write doc9303 instance data in XML file
    
        @param doc: doc9303
        @type doc: doc9303 instance (pyPassport)
        @param filename: output file
        @type filename: String
        @return: None        
    """
    xml = Document()
    root = xml.createElement("Files")
    xml.appendChild(root)
    
    def recursiveFill(node, root):
        """ Write node recursively
        
            @param node: data
            @type node: dictionary
            @param root: xml root node for data
            @type root: xml Node
            @return: None
        """
        # is a dictionary
        if  isinstance(node,types.DictType):
            for item in node:
                elem = xml.createElement("Tag")
                elem.setAttribute("Value", str(item))
                try:
                    elem.setAttribute("Name", tagToName[item])
                except KeyError, msg:
                    print "Cannot resolve tag", item
                root.appendChild(elem)
                recursiveFill(node[item], elem)
        # is non-empty list of values (not hexlist)
        elif isinstance(node,types.ListType) and len(node) > 0 and type(node[0]) != types.IntType:
            for i in range(len(node)):
                elem = xml.createElement("Item")
                elem.setAttribute("Value", str(i))
                root.appendChild(elem)
                recursiveFill(node[i], elem)
        # is an item (leaf)
        else:
            if isPrintable(str(node)):
                txt = xml.createTextNode(str(node))
                root.setAttribute("Format", "Bin")
                root.appendChild(txt)
            else:
                node = binToHexRep(str(node))
                root.setAttribute("Format", "HexRep")
                data = xml.createTextNode(node) #xml.createCDATASection
                root.appendChild(data)
                
    recursiveFill(doc, root)    
    
    file = open(filename,"w")
    xml.writexml(file)
    file.close()
    
def isPrintable(txt):
    """ Test if each character of txt is printable
    
        @param txt: text to test
        @type txt: String
        @rtype: Boolean
    """
    import string
    for c in txt:
        if c not in string.printable:
            return False
    return True

def toPDF(data, filename):
    """ Export doc9303 instance to PDF
    
        @param doc: doc9303
        @type doc: doc9303 instance (pyPassport)
        @param filename: output file
        @type filename: String
        @return: None 
    """
    
    
    
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    Story=[]
    styles=getSampleStyleSheet()
    
    # NAME
    name = (data["EP"]["DG1"]["5F5B"]).split("<<")
    Story.append(Paragraph(getItem(name[1].upper())+" "+getItem(name[0].upper()), styles["Heading1"]))
    
    # PICTURE
    tag = None
    if data["EP"]["DG2"]["A1"].has_key("5F2E"): tag = "5F2E"
    elif data["EP"]["DG2"]["A1"].has_key("7F2E"): tag = "7F2E"
    if tag != None: 
        path = None
        raw = data["EP"]["DG2"]["A1"][tag]
        profile = writeImageToDisk(raw, "~picture")
        img_file = PIL.Image.open(profile)
        width, height = img_file.size
        ratio = float(width)/float(2*inch)
        h_img = float(height)/ratio
        im = Image(profile, 2*inch, h_img)
        Story.append(im)
    
    try:
        if data["EP"].has_key("DG7") and data["EP"]["DG7"].has_key("5F43"):
            raw = data["EP"]["DG7"]["5F43"][0]
            signature = writeImageToDisk(raw, "~signature")
            img_signature = PIL.Image.open(signature)
            width, height = img_signature.size
            ratio = float(width)/float(2*inch)
            h_img = float(height)/ratio
            sign = Image(signature, 2*inch, h_img)
            Story.append(sign)
    except Exception:
        pass
     
    # OVERVIEW
    Story.append(Paragraph("Overview", styles["Heading2"]))
    Story.append(Paragraph("<font size=12>Type: " + getItemByTag(data["EP"], 'DG1','5F03') + "</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Passport #: "+str(getItemByTag(data["EP"],'DG1','5A'))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Country: "+str(getItemByTag(data["EP"],'DG1','5F28'))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Authority: "+str(getItemByTag(data["EP"],'DG12','5F19'))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Issue Date: "+str(getItemByTag(data["EP"],'DG12','5F26'))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Expiry Place: "+str(getItemByTag(data["EP"],'DG1','59'))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Nationality: "+str(getItemByTag(data["EP"],'DG1','5F2C'))+"</font>", styles["Normal"]))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("<font size=12>Name: "+str(getItem(name[0]))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Surname: "+str(getItem(name[1]))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Birth Date: "+str(getItemByTag(data["EP"],'DG1','5F57'))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Birth Place: "+str(getItemByTag(data["EP"],'DG11','5F11'))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Sex: "+str(getItemByTag(data["EP"],'DG1','5F35'))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Height: "+str(getItemByTag(data["EP"], 'DG13', '9F01'))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Colour of eyes: "+str(getItemByTag(data["EP"], 'DG13', '9F02'))+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Residence: "+str(getItemByTag(data["EP"], 'DG13', '9F03'))+"</font>", styles["Normal"]))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("Basic Access Control", styles["Heading2"]))
    Story.append(Paragraph("<font size=12>Basic Access Control: "+data["bac"]+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Reading time: "+str(data["ReadingTime"])+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Data Groups size:</font>", styles["Normal"]))
    for key, value in data["DGs"]:
        Story.append(Paragraph("<font size=12>&nbsp;&nbsp- " + str(key) + ": " + str(value) + " octets"+"</font>", styles["Normal"]))
    # PRESENT DATAGROUPS
    #Story.append(Paragraph("Present DataGroups", styles["Heading2"]))
    #k = map(toOrder, data["EP"].keys())
    #k.sort()
    #k = map(toDG,k)
    #for dg in k:
    #    Story.append(Paragraph("<font size=12>&nbsp;&nbsp;- "+str(dg)+"</font>", styles["Normal"]))
    #Story.append(Spacer(1, 20))

    # DUMP
    Story.append(Paragraph("MRZ information", styles["Heading3"]))
    for item in data["EP"]["DG1"]:
        try:
            tag_name = tagToName[item]
        except Exception:
            tag_name = item
        Story.append(Paragraph("<font size=12>&nbsp;&nbsp;&nbsp;&nbsp;"+tag_name+": "+getItemRaw(data["EP"], 'DG1', item)+"</font>", 
                                styles["Normal"]))
    Story.append(Spacer(1, 12))
    
    if data["EP"].has_key("DG11"):
        Story.append(Paragraph("Additional document holder details", styles["Heading3"]))
        for item in data["EP"]["DG11"]["5C"]:
            try:
                tag_name = tagToName[item]
            except Exception:
                tag_name = item
            Story.append(Paragraph("<font size=12>&nbsp;&nbsp;&nbsp;&nbsp;"+tag_name+": "+getItemRaw(data["EP"], 'DG11', item)+"</font>", 
                                    styles["Normal"]))
        Story.append(Spacer(1, 12))
    
    if data["EP"].has_key("DG12"):
        Story.append(Paragraph("Additional document information", styles["Heading3"]))
        for item in data["EP"]["DG12"]["5C"]:
            try:
                tag_name = tagToName[item]
            except Exception:
                tag_name = item
            Story.append(Paragraph("<font size=12>    "+tag_name+": "+getItemRaw(data["EP"], 'DG12', item)+"</font>", 
                                    styles["Normal"]))
        Story.append(Spacer(1, 12))
    
    if data["EP"].has_key("DG13"):
        Story.append(Paragraph("Reserved for national specific data", styles["Heading3"]))
        for item in data["EP"]["DG13"]["5C"]:
            try:
                tag_name = tagToName[item]
            except Exception:
                tag_name = item
            Story.append(Paragraph("<font size=12>&nbsp;&nbsp;&nbsp;&nbsp;"+tag_name+": "+getItemRaw(data["EP"], 'DG13', item)+"</font>", 
                                    styles["Normal"]))
        Story.append(Spacer(1, 12))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph("Passive Authentication", styles["Heading2"]))
    Story.append(Paragraph("DG intergrity:", styles["Heading3"]))
    for dgi in data["Integrity"]:
        v = ("Verified") if data["Integrity"][dgi] else ("Not verified")
        Story.append(Paragraph("<font size=12>  "+dgi+": "+v+"</font>", styles["Normal"]))
    Story.append(Paragraph("DG hashes:", styles["Heading3"]))
    for dgi in data["Hashes"]:
        Story.append(Paragraph("<font size=12>  "+dgi + ": " + binToHexRep(data["Hashes"][dgi])+"</font>", styles["Normal"]))
    
    Story.append(Paragraph("SOD", styles["Heading3"]))
    Story.append(Paragraph("<font size=10>"+data["SOD"].replace("\n", "<br/>")+"</font>", styles["Normal"]))
    
    Story.append(Paragraph("Certificate", styles["Heading3"]))
    Story.append(Paragraph("<font size=12>Certificate Serial Number:"+data["certSerialNumber"]+"</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Certificate Fingerprint:"+data["certFingerPrint"]+"</font>", styles["Normal"]))
    
    Story.append(Paragraph("Document Signer", styles["Heading3"]))
    data["DSCertificate"] = data["DSCertificate"].replace("\n", "<br/>")
    data["DSCertificate"] = data["DSCertificate"].replace(" ", "&nbsp;")
    Story.append(Paragraph("<font size=10>"+data["DSCertificate"]+"</font>", styles["Normal"]))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph("Active Authentication", styles["Heading2"]))
    Story.append(Paragraph("<font size=12>Active Authentication executed:"+data["activeAuth"]+"</font>", styles["Normal"]))
    Story.append(Paragraph("Public Key", styles["Heading3"]))
    data["pubKey"] = data["pubKey"].replace("\n", "<br/>")
    data["pubKey"] = data["pubKey"].replace(" ", "&nbsp;")
    Story.append(Paragraph("<font size=10>"+data["pubKey"]+"</font>", styles["Normal"]))
    
    Story.append(Paragraph("Extended Access Control", styles["Heading2"]))
    Story.append(Paragraph("<font size=12>EAC has not been implemented yet.</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Here is of DG that the reader cannot access:</font>", styles["Normal"]))
    for fdg in data["failedToRead"]:
        Story.append(Paragraph("<font size=12>&nbsp;&nbsp;- " + fdg + "</font>", styles["Normal"]))
    if not data["failedToRead"]:
        Story.append(Paragraph("<font size=12>&nbsp;&nbsp; List empty: No EAC implemented in passport</font>", styles["Normal"]))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph("Security investigation", styles["Heading2"]))
    Story.append(Paragraph("Security measures", styles["Heading3"]))
    Story.append(Paragraph("<font size=12>Delay security measure after a wrong BAC: " + str(data["delaySecurity"]) + "</font>", styles["Normal"]))
    Story.append(Paragraph("<font size=12>Block the communication after a wrong BAC: " + str(data["blockAfterFail"]) + "</font>", styles["Normal"]))
    
    Story.append(Paragraph("Potential vulnerabilities", styles["Heading3"]))
    (vuln, ans) = data["activeAuthWithoutBac"]
    Story.append(Paragraph("<font size=12>Active Authentication before BAC: " + str(vuln) + "</font>", styles["Normal"]))
    if vuln: Story.append(Paragraph("<font size=12>&nbsp;&nbsp;* Vulnerable to AA Traceability</font>", styles["Normal"]))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("<font size=12>Active Authentication before BAC: " + str(vuln) + "</font>", styles["Normal"]))
    if vuln: Story.append(Paragraph("<font size=12>&nbsp;&nbsp;* Vulnerable to AA Traceability</font>", styles["Normal"]))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("<font size=12>Diffirent repsonse time for wrong message or MAC: " + str(data["macTraceability"]) + "</font>", styles["Normal"]))
    if data["macTraceability"]: 
        Story.append(Paragraph("<font size=12>&nbsp;&nbsp;* Vulnerable to MAC traceability</font>", styles["Normal"]))
        Story.append(Paragraph("<font size=12>&nbsp;&nbsp;&nbsp;&nbsp;Note: If delay security measure implemented, this might be a false positive</font>", styles["Normal"]))
    Story.append(Spacer(1, 12))
    (vuln, error) = data["getChallengeNull"]
    Story.append(Paragraph("<font size=12>Passport answer to a GET CHALLENGE with the Le set to '00': " + str(vuln) + "</font>", styles["Normal"]))
    if vuln: Story.append(Paragraph("<font size=12>&nbsp;&nbsp;* Vulnerable to lookup brute force</font>", styles["Normal"]))
    
    Story.append(Paragraph("Error Fingerprinting", styles["Heading3"]))
    for ins in data["Errors"]:
        Story.append(Paragraph('<font size=12>APDU "00" "' + ins + '" "00" "00" "" "" "00": ' + data["Errors"][ins] + "</font>", styles["Normal"]))

    
    doc.build(Story)
    
    if tag != None:
        os.remove(profile)
        os.remove(signature)
    
    

def browseDGs(data, level=0):
    dgtypes = [DataGroup1, DataGroup2, DataGroup3, DataGroup4, DataGroup5,
               DataGroup6, DataGroup7, DataGroup8, DataGroup9, DataGroup10,
               DataGroup11, DataGroup12, DataGroup13, DataGroup14, DataGroup15,
               DataGroup16, Com, SOD]
    i = level
    if type(data) == type(dict()) or type(data) in dgtypes:
        for x in data:
            Story.append(Paragraph("<font size=12>  "+truncate(x, i*"  "), styles["Normal"]))
            if type(data[x]) == type(dict()) or type(data[x]) == type(list()) or type(data[x]) in dgtypes:
                self.browseDGs(data[x], i+1)
            else:
                Story.append(Paragraph("<font size=12>  "+truncate(data[x], (i+1)*"  "), styles["Normal"]))
                
    elif type(data) == type(list()):
        for x in data:
            if type(x) == type(dict()) or type(x) == type(list()) or type(x) in dgtypes:
                self.browseDGs(x, i+1)
            else:
                Story.append(Paragraph("<font size=12>  "+truncate(x, (i+1)*" "), styles["Normal"]))

def truncate(data, sep="  ", length=200):
    return sep + (str(data)[:length] + '..') if len(str(data)) > length else sep + str(data)
