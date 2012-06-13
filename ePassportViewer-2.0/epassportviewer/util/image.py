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

import os
import base64, zlib
import Image
import cStringIO

from epassportviewer.util.singleton import Singleton
from pypassport import jp2converter

def convertImage(data):
    """ Convert any Image into a compatible image byte stream 
    
        @param data: raw image
        @type data: binary representation
        @return: jpg or bmp image
        @rtype: StringIO
    """
    img = None
    try:
        img = jp2converter.ConvertJp2(data)
    except Exception, msg:
        print msg
    if img: data = img
    imgBin = cStringIO.StringIO(data)
    return imgBin

def writeImageToDisk(data, filename):
    """ write image to disk
        jpg as jpg and jp2 as bmp 
        
        @param data: raw image
        @type data: binary representation        
        @param filename: path to output file (without extension)
        @type filename: String
        @return: filename with corresponding extension
        @rtype: String
    """
    
    img = jp2converter.ConvertJp2(data)
    if img: 
        filename = filename + ".bmp"
        data = img
    else:
        filename = filename + ".jpg"

    try:
        f = open(filename,"wb")
        try:
            f.write(data)
        finally:
            f.close()
    except IOError:
        pass
    
    return filename

class ImageFactory(Singleton):
    
    transparent = """\
    eJzrDPBz5+WS4mJgYOD19HAJAtIngJiRgw1Izt7/8BGIUxzk7sSw7pzMSyCHLcnb3YXhPwgu2Lt8
    MlCEs8AjspiBgVsYhBkZZs2RAAqyl3j6urLfZGYTYDPOa1q+GijEUeIaUeKcn5ubmlfC8O3MtP1A
    MQFPF8cQjfPJCRKsixNEHrAwMCsyMEqKzHwHlGPwdPVzWeeU0AQA8IoqnA==
    """
    
    app = """\
    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
    Gg2ncIHeEqx/T0VJ412dgkXE/wHmujqJ
    """
    
    error = """\
    eJwBSwK0/YlQTkcNChoKAAAADUlIRFIAAAAQAAAAEAgGAAAAH/P/YQAAAARnQU1BAACvyDcFiukA
    AAAZdEVYdFNvZnR3YXJlAEFkb2JlIEltYWdlUmVhZHlxyWU8AAAB3UlEQVQ4y6WTa2saQRSG92tI
    ICEppjSEll5jm6CoocaYFDRljUqb2kukaSi90cv/zIdcIH+jxJWgss6uuztPZ1Y3VZSW0g8vC8O+
    z5n3nDMGYPyPxg8NwwqPBwpGZf0ZYBgNHt2H7+/g2wHy61vklzry0xvkh1f4D27jGUZ7MiAy/zgE
    s4jMZJCpFEEySbC2hp/P4h8+p3fvJkL/OwIYNh/U4fwcWasRJBIEq6v4lQry7AyvWsLb38W9s4w9
    gESA/pVVZW2m04FmE79axS+XwVLR223kyQm9xEN6Lwp0QusQIMybThPs7YXmCBJKmxWkt72Ns7iI
    ++wJrWGA7rD8vP87r7pyZAylzO7WFk4shlhYwKnkJwA+vu7njcfxS6URgK7u5nKI+Xm6s7M4pew4
    IHhfw19ZwTfNq8z6q820WsiLC4SajD09jfN0ncthgKcBakTe4xTy9LRftdHA3dzE2dgIzVJBgqMj
    usvXEcX0KMBVG6bn69XLeGaB4Pg4NOu83bk5hG6uMov1JGInQ3vpGk3D+DmySGo5LD3f3ssd3Pjd
    q7z2zAz21BT2Uiys3Boyj62yWg7LvnUDt5rH2c3hmNkwryhmEIXUmHniY1LdtXSHI10O1Oyr+ffX
    +I/6BeeVuIP9nt2/AAAAAElFTkSuQmCCn+Ac/A==
    """
    
    tick = """\
    eJwBDQPy/IlQTkcNChoKAAAADUlIRFIAAAAQAAAAEAgGAAAAH/P/YQAAAARnQU1BAACvyDcFiukA
    AAAZdEVYdFNvZnR3YXJlAEFkb2JlIEltYWdlUmVhZHlxyWU8AAACn0lEQVQ4y6WT60tTYRzH/Tt2
    znZsAwlkRCGChFB7FSQSO5oNxbwsS9PdvdI2Y9hMizJyXsZIKS2z1GpzTm3q1ObWlDJx2VFCzL3p
    QrVhdLFv5+zFTBIjeuALDw/P5/N7rnEA4v4nfwwU+A6JcqcP6rM9KUzG4/1h6Yg4LHUlMlJnoj7d
    vle0qyDPm0rLPMkhnUeGm0EL+pa7oulcbEaJ6xgkvVRI0kPROwrYqnTmeFLk6pwRztV+2F5eg2mu
    Mhqu71jtQ+NMFQ7Y+JFkG5/eJsjxpAgz3UnrHMxNrAmUocJfAs3MGejYlLOp9p2F/fU9XJyqgNhC
    rouvk8KYQOZOMqjGsqKVOZgDVd5TUEwXQjFVAPVUIdxrgzB4lXCwktyeI0i4QhpigowRMdMZbIY1
    2IQKXzGUT+QsmA/lJBtPPsbfuMC1UGQNbc8bYZtrRHw9ycQER+0JGw9WbqM2oIHWW8SuZACLH+ah
    mijE2NpQFP6x+R1tzy7BMFGMvmAnBEZiIyaQ3Kc2+pe7YfSrUOvX4tPXj1Ho/Ze3MdgyWw+1Kxt6
    92n0BzsgqPld0EMxN+ab0L5wGbpJOcy+akS+fY7Cmz83YXl6AWXOLGhYQUugDu1eM6gqYmsLqbcE
    BvlAGuwrd1E9IYfafRJ10+VYereAttkGlA4eh8JxAjpnDuyvupFuPQyqktg6xGQrX7iPvRqzR4OH
    zB1UjuZBO5wD1ZAMSgcXDs7Go6UuGIeKIVDz1ik1Idz2kBKbSDq+gYiY3GVwsJLWgBn60SKcG5aj
    ld2CnYX1ziLwS3kRFqZ3fMp7GkiaMhEhaYcE7X4zel9Y0TtvhcVrQlpLKgQKXohSEfSun4k6T4oo
    A6GnaghGoOWFBSpemK3IsNFTpYTor7/xX/MLZ9Cs5Xm61GMAAAAASUVORK5CYIL+GmIC
    """
    
    help = """\
    eJwBEgPt/IlQTkcNChoKAAAADUlIRFIAAAAQAAAAEAgGAAAAH/P/YQAAAARnQU1BAACvyDcFiukA
    AAAZdEVYdFNvZnR3YXJlAEFkb2JlIEltYWdlUmVhZHlxyWU8AAACpElEQVQ4y6WT3U+SYRjG/Vvg
    T2it5mrVap3V1jjooAOn5ifQ1HK1DJazdJjTLCk1M50KauqcigJvAiKIJsqXIPBiIl/Kx0R44VWz
    7eqNNZzL2VoHv5N7z/Xbrmf3nQMg53/4Y6AjD9la94FA49wnVes09cWeohQ2ipyxJARTpj32mQK1
    k+bMOtIhT/gQGzs03EEqg2c7DUcgjZHFaGhoIcw5VUCspThyazK1GdmH+dsupHN+iMacqB9ZRxex
    AYMjCleIwieVP9VFbHFOCGTmBGtyNR7cCNNYcMZQy4Q6CQ/8MRq+WBpjiwHUSK1QroZg9yXQOkkG
    m8ddrKxgdCkqXPOnsOKJQzhox+MeM9IHRww/fnOE2kELavpNmLdHoF2LoE5qFWYFfXMh0sV07SY2
    Ud1jQlX3CvzRNKaWA1DbtkEzArUtCG67Dq1TDli9u3jSbSSzgg6Fl3YHkxBKLKj8aASv08A81mPa
    6MMudYCdXRq9sy6UtmlR+UEPh28PPLGezgpaxl20K5DE0wELuB16lL/XoeydDkn6O7YiFPhiLYpa
    VLjPwBdrYPfHkd+kPha8kNpI21YcYpkLvHYDysTzKHk7h+LX6gyFrwgUNipQ0ChHvXQZRk8Ed+vk
    xxWYPkKFMQC9I4LKDkM2GEvsI7JHI080k6FQJAOx6oOEqXOrZuL4E/niBVb5m/ngkjMC5Yof3DYN
    CpqUaBs3ZfgVzm+YwLDGDY0lgJvVY8HrD0dZJxYpTzTLuddApHT2baitQbyULKGkWY6ixmk879VD
    afRCZfbjasXn1OUHQ5xTV/mOUMa5/Wwy1Ees46s7DIs3lmHRuYMumQ25PGnoYrmEc+Yx3Xg0yr5W
    NSK4UjFMXuIPUrlcKXWhbIA8X9ovOFfcx/7rNf4rPwHXrwWivU29xAAAAABJRU5ErkJggvhWYds=
    """
    
    logo = """\
    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
    """
    
    gsi = """\
    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
    1iI+uQmLAlgAAAAASUVORK5CYIJ17dCA
    """
    
    HELP, APP, TICK, ERROR, TRANSPARENT, LOGO, GSI = ('help','app','tick','error','transparent', 'logo', 'gsi')
    TYPES = [HELP, APP, TICK, ERROR, TRANSPARENT, LOGO, GSI]
    
    
    def initialize(self):
        self.index = {'help'        : self.help,
                      'app'         : self.app,
                      'tick'        : self.tick,
                      'error'       : self.error,
                      'transparent' : self.transparent,
                      'logo'        : self.logo,
                      'gsi'         : self.gsi
                      }
    
    def create(self, type):
        if type not in self.TYPES:
            raise Exception("Unknown Image")
        
        return cStringIO.StringIO(zlib.decompress(base64.b64decode(self.index[type])))

def make(path):
#    jpgfile = path
#    im = Image.open(jpgfile)
#    holder = cStringIO.StringIO()
##    im.save(holder, format="png", transparency=255)
#    bytes_string = holder.getvalue()
    bytes_string = open(path, 'rb').read()
    jpg_text = '"""' + base64.encodestring(zlib.compress(bytes_string)) + '"""'
    print jpg_text
    
    
def view(name):
    img = Image.open(ImageFactory().create(name))
#    holder = cStringIO.StringIO()
#    img.save(holder, format='png', transparency=255)
    img.show()


#make('gsi.png')
