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

import types
import os

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from string import replace
from xml.dom.minidom import Document, parse

from pypassport.hexfunctions import *
from pypassport.doc9303.converter import toDG, toOrder
from pypassport.doc9303.tagconverter import tagToName
from pypassport.jp2converter import jp2ConverterException
from epassportviewer.util.image import writeImageToDisk
from epassportviewer.util.helper import getItem, getItemByTag

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

def toPDF(doc, filename):
    """ Export doc9303 instance to PDF
    
        @param doc: doc9303
        @type doc: doc9303 instance (pyPassport)
        @param filename: output file
        @type filename: String
        @return: None 
    """
    
    pdf = Canvas(filename)
    # Font
    pdf.setFont("Courier", 26)
    # Line Color
    pdf.setStrokeColorRGB(0.5, 0.5, 0)
    # Text Color
    pdf.setFillColorRGB(0, 0, 0)
    
    pdf.setFont("Courier", 9)
    pdf.drawString(pdf._pagesize[0]/2, cm, "generated by ePassport Viewer")
    
    height = pdf._pagesize[1]
    
    tag = None
    if doc['75']["A1"].has_key("5F2E"): tag = "5F2E"
    elif doc['75']["A1"].has_key("7F2E"): tag = "7F2E"
    if tag != None: 
        path = None
#        try:
        data = doc['75']["A1"][tag]
        path = writeImageToDisk(data, "~picture")
        pdf.drawImage(path, pdf._pagesize[0] - 200, pdf._pagesize[0] - 150, 150, preserveAspectRatio=True)
#        except Exception, msg:
#            pass
    
    pdf.setFont("Courier", 12)
    
    def addLine(rhyme, key, value=None):
        if value == None: value = ""
        try:
            rhyme.textLine(str(key)+str(value))
        except Exception, msg:
            pass
            #TODO: Handle Exception ?
    
    name = (doc['61']['5F5B']).split("<<")    
    rhyme = pdf.beginText(cm, height - 50)
    addLine(rhyme, "Overview")
    addLine(rhyme, "  Type: ", getItemByTag(doc, '61','5F03'))
    addLine(rhyme, "  Country: ", getItemByTag(doc,'61','5F28'))
    addLine(rhyme, "  PassportNumber: ", getItemByTag(doc,'61','5A'))
    addLine(rhyme, "  Nationality: ", getItemByTag(doc,'61','5F2C'))
    addLine(rhyme, "  Name: ", getItem(name[0]))
    addLine(rhyme, "  Surname: ", getItem(name[1]))
    addLine(rhyme, "  Birth Date: ", getItemByTag(doc,'61','5F57'))
    addLine(rhyme, "  Birth Place: ", getItemByTag(doc,'6B','5F11'))
    addLine(rhyme, "  Sex: ", getItemByTag(doc,'61','5F35'))
    addLine(rhyme, "  Authority: ", getItemByTag(doc,'6C','5F19'))
    addLine(rhyme, "  Issue Date: ", getItemByTag(doc,'6C','5F26'))
    addLine(rhyme, "  Expiry Place: ", getItemByTag(doc,'61','59'))
    addLine(rhyme, "")        
    addLine(rhyme, "")
    addLine(rhyme, "Present DataGroups")
            
    # Present Datagroup in order
    k = map(toOrder, doc.keys())
    k.sort()
    k = map(toDG,k)
    rhyme.textLine("")
    for dg in k:
        rhyme.textLine("  >> "+str(dg))

    pdf.drawText(rhyme)        
    pdf.showPage()
    pdf.save()

if __name__ == "__main__":
    from pyPassport.doc9303.doc9303 import doc9303
    path = "/home/oroger/workspace/pyPassport/src/data/dump/Test"
    doc = doc9303(None, path)
    toPDF(doc, "/home/oroger/Bureau/PDF.pdf")
    toXML(doc, "/home/oroger/Bureau/XML.xml")