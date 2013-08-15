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

from pypassport import pki
from pypassport import hexfunctions
from pypassport.genpassport import datagroupcreation
from pypassport.genpassport import jcop
from pypassport.doc9303 import datagroup, converter
from epassportviewer.util import readerAbstract

def generate(   firstname,
                surname,
                sex,
                dob,
                nationality,
                id_doc,
                doe,
                issuer,
                face_path,
                country,
                organisation,
                pob,
                middle_name,
                issuing_auth,
                doi,
                height,
                eyes,
                address,
                update = True,
                cap_path = None):


    if firstname == "": firstname = "John"
    if surname == "": surname = "Doe"
    if sex == "": sex = "M"
    if dob == "YYYY/MM/DD": dob = "1970/01/01"
    if nationality == "": nationality = "BEL"
    if id_doc == "": id_doc = "EH123456"
    if doe == "YYYY/MM/DD": doe = datetime.date.today().strftime("%Y/%m/%d")
    if issuer == "": issuer = "BEL"
    if face_path == "": face_path = "epassportviewer/ressources/face.jpg"
    if country == "": country = "BEL"
    if organisation == "": organisation = "UCL"
    if doi == "YYYY/MM/DD": doi = None


    date_cmp = doe.split("/")
    doe = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))

    date_cmp = dob.split("/")
    dob = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))


    ###################
    #       CA        #
    ###################

    # Create a fake Country Signer Certification Authority
    CSCA = pki.DistinguishedName(C=country[:2], O=organisation, CN="CSCA")

    # Create a fake Document Signer bond to CSCA
    DS = pki.DistinguishedName(C=country[:2], O=organisation, CN="Document-Signer")

    ca = pki.CA()
    (csca, cscaKey) = ca.createCSCA(1024, 720, CSCA)
    (ds, dsKey) = ca.createDS(1024, 365, DS)


    ###################
    #    DATAGROUP    #
    ###################



    # Create DataGroup 1 (MRZ) [mandatory]
    dg1 = datagroupcreation.DataGroup1Creation().create("P", issuer, surname, firstname, nationality, sex, id_doc, dob.strftime("%d%m%y"), doe.strftime("%d%m%y"))

    # Create DataGroup 2 (Face) [Mandatory]
    dg2 = datagroupcreation.DataGroup2Creation().create(face_path)

    dgs = [dg1, dg2]

    # Create DataGroup 11 (Additional document holder information) [Optional]
    if pob or middle_name:
        dgc = datagroupcreation.DataGroupFileCreation(converter.toTAG("DG11"))
        content = ""

        # Full name
        if middle_name:
            middle_name = middle_name.replace(' ', '<')
            full_name = surname.upper() + "<<" + firstname.upper() + middle_name.upper()
            dgc.addDataObject("5F02", full_name)

        # Place of birth
        if pob:
            pob = pob.replace(' ', '<')
            dgc.addDataObject("5F11", pob)
            content += "5F11"

        dgc.addDataObject("5C", hexfunctions.hexRepToBin("5F11"))

        dg11 = datagroup.DataGroupFactory().create(dgc)
        dgs.append(dg11)

    # Create DataGroup 12 (Additional document information) [Optional]
    if issuing_auth or doi:
        dgc = datagroupcreation.DataGroupFileCreation(converter.toTAG("DG12"))
        content = ""

        # Issuing authority
        if issuing_auth:
            dgc.addDataObject("5F19", issuing_auth)
            content += "5F19"
        # Date of issue
        if doi:
            date_cmp = doi.split("/")
            doi = datetime.date(int(date_cmp[0]), int(date_cmp[1]), int(date_cmp[2]))

            dgc.addDataObject("5F26", doi.strftime("%Y%m%d"))
            content += "5F26"

        dgc.addDataObject("5C", hexfunctions.hexRepToBin(content))

        dg12 = datagroup.DataGroupFactory().create(dgc)
        dgs.append(dg12)

    # Create DataGroup 13 (Reserved for national specific data) [Optional]
    if height or eyes or address:
        print "DG13"
        dgc = datagroupcreation.DataGroupFileCreation(converter.toTAG("DG13"))

        content = ""

        # Height
        if height:
            dgc.addDataObject("9F01", height)
            content += "9F01"
        # Eyes
        if eyes:
            dgc.addDataObject("9F02", eyes)
            content += "9F02"
        # Address
        if address:
            dgc.addDataObject("9F03", address)
            content += "9F03"

        dgc.addDataObject("5C", hexfunctions.hexRepToBin(content))

        dg13 = datagroup.DataGroupFactory().create(dgc)
        dgs.append(dg13)




    # Create presence map [mandatory]
    com = datagroupcreation.ComCreation().create(dgs)
    # Create a signer data strcture [mandatory]
    sod = datagroupcreation.SODCreation().create(ds, dsKey, dgs)

    dgs.append(com)
    dgs.append(sod)


    ###################
    #      JCOP       #
    ###################

    # Initializing the GPlatform object with the reader #1
    if not update:
        jc = jcop.GPlatform(reader_nb)
        jc.install(cap_path)

    r = readerAbstract.waitForCard()
    jcw = jcop.JavaCardWritter(r)


    # Write the forged ePassport in the JCOP
    for dg in dgs:
        jcw.writeDG(dg)
    jcw.setKseed(dg1)


