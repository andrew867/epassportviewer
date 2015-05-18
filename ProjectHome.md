In 2004, the [ICAO](http://en.wikipedia.org/wiki/International_Civil_Aviation_Organization) published a new version of [Doc9303](http://www2.icao.int/en/MRTD/Pages/Doc9393.aspx) that defines the specifications of the [electronic passports](http://en.wikipedia.org/wiki/Biometric_passport), known as ePassports. These passports, easily recognizable with their logo on the front cover, contain a passive contactless chip featured with some cryptographic mecanisms.

_ePassport_ _Viewer_ is a GPL-friendly tool to read and checks ePassports, developped by Jean-Francois Houzard and Olivier Roger during their Master Thesis achieved in the [Information Security Group](http://www.uclouvain.be/sites/security/) of the [UCL](http://www.uclouvain.be) in Belgium.
_ePassport_ _Viewer_ is currently available as beta version.

## News ##
|Sep, 2009|Version 1.0 of ePassport Viewer released|[Windows](http://epassportviewer.googlecode.com/files/epassportviewer-1.0.win32.zip) [MacOSX](http://epassportviewer.googlecode.com/files/epassportviewer-1.0.osx.dmg) [Source](http://epassportviewer.googlecode.com/files/epassportviewer-1.0.zip)|
|:--------|:---------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|May 18, 2009|Version 0.2c of ePassport Viewer released|[Windows](http://epassportviewer.googlecode.com/files/epassportviewer-0.2c.win32.zip) [MacOSX](http://epassportviewer.googlecode.com/files/epassportviewer-0.2c.osx.dmg) [Source](http://epassportviewer.googlecode.com/files/epassportviewer-0.2c.zip)|
|May 1, 2009|First Public Release                    |


---

## ePassport Viewer ##

_ePassport_ _Viewer_ is a GUI built on top of [pyPassport](http://code.google.com/p/pypassport/). The software provides the following functionality:

  * Read and display the results;
  * Save/Load a dump;
  * Export subset of data (Picture, Signature, Public key, Certificate);
  * Export a summary in XML or PDF format;
  * Make a "fingerprint" of the passport;
  * Verify the data's authenticity and integrity.

_ePassport_ _Viewer_ is released under [GNU General Public License, Version 3](http://www.gnu.org/licenses/gpl-3.0.txt) License.


---

## Disclaimer ##

Before using _ePassport_ _Viewer_, you must be sure that you are allowed to read the contactless chip of your passport, according to the laws and regulations of the country that issued it.


---

## Documentation ##

  * [User Manual](http://epassportviewer.googlecode.com/files/epassportviewer-0.2c.manual.pdf)
  * [Installation Instructions](http://code.google.com/p/epassportviewer/wiki/Installation_Instructions)
  * SmartCard\_Service\_Deamon: smartcard.pcsc.PCSCExceptions.EstablishContextException
  * [OpenSSL](http://code.google.com/p/epassportviewer/wiki/OpenSSL): The security labels are orange
  * [Hardware Compatibility](http://code.google.com/p/pypassport/wiki/Hardware_Compatibility)


---

## IRIS PEN Express ##
[IRISPEN express](http://www.irislink.com/c2-1052-189/IRISPen-scanner---Ideal-pen-scanner-for-printed-text-retyping-.aspx) is a product from the [IRIS](http://www.irislink.com/) company, specialized in OCR technology. This pen allows to scan the passport MRZ and fill the application in a single move. This become very handy if you need to do it frequently.

[![](http://www.irislink.com/Documents/Images/200510281646/iris_logo_150x87_fr%5B1%5D.gif)](http://www.irislink.com/) [![](http://www.irislink.com/Documents/Image/products/irispen/resize_new.jpg)](http://www.irislink.com/c2-1052-189/IRISPen-scanner---Ideal-pen-scanner-for-printed-text-retyping-.aspx)


---

## Links ##
The [JMRTD](http://jmrtd.org/csca.shtml) website list some Country Signing Certificates found using [Google](http://www.google.com).

You can learn more about electronic passports: [Belgian Biometric Passport does not get a pass...](http://www.dice.ucl.ac.be/crypto/passport/index.html) by Gildas Avoine, Kassem Kalach, and Jean-Jacques Quisquater (2007).


---

## Related softwares ##

  * [Golden Reader Tool](http://www.bsi.de/literat/faltbl/F25GRT.htm) by BSI
  * [JMRTD](http://www.jmrtd.org/): A Free Implementation of Machine Readable Travel Documents (JAVA)
  * [RFIDIOt](http://www.rfidiot.org/): RFID tools (Python)
  * [wzMRTD](http://www.waazaa.org/wzpass/index.php?lang=en): ePassport API by Johann Dantant (C++)


---

## Acknowledgment ##

We would like to thank J.-P. Szikora, A. Laurie, M. Oostdijk, I. Etingof, Ph. Teuvens, and M. Vuagnoux for their comments or advices.