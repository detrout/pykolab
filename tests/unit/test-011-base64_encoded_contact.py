from email import message_from_string
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEImage import MIMEImage
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import sys
import unittest

class TestContactBase64EncodedXML(unittest.TestCase):
    def assertIsInstance(self, _value, _type):
        if hasattr(unittest.TestCase, 'assertIsInstance'):
            return unittest.TestCase.assertIsInstance(self, _value, _type)
        else:
            if (type(_value)) == _type:
                return True
            else:
                raise AssertionError, "%s != %s" % (type(_value), _type)

    def test_001_base64_encoded_xml(self):
        msg = """From: vanmeeuwen@demo.kolab.org
Reply-To:
Bcc:
To: synckolab@no.tld
Subject: sk-vc-3AC0C113BFADC313
Date: Sun, 17 Feb 2013 10:21:40 -0500
Content-Type: Multipart/Mixed;boundary="Boundary-00=363B189F14E3799C"
User-Agent: SyncKolab 3.0.0
X-Kolab-Type: application/vcard+xml

--Boundary-00=363B189F14E3799C
Content-Type: Text/Plain;
 charset="us-ascii"
Content-Transfer-Encoding: 7bit

This is a Kolab Groupware object.
To view this object you will need an email client that can understand the Kolab Groupware format.
For a list of such email clients please visit
http://kolab.org/content/kolab-clients
---
Name: van Meeuwen Jeroen
E-Mail:kanarip@kanarip.com
---

Notice:
The information above is only valid, if no other client than synckolab updated this message. (ie. a client that updates the attachment but not the message)

--Boundary-00=363B189F14E3799C
Content-Type: application/vcard+xml;
 name="kolab.xml"
Content-Transfer-Encoding: base64
Content-Disposition: attachment;
 filename="kolab.xml"

PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIiA/
Pgo8dmNhcmRzIHhtbG5zPSJ1cm46aWV0ZjpwYXJhbXM6eG1sOm5zOnZjYXJkLTQuMCI+Cjx2
Y2FyZD4KIDx1aWQ+PHRleHQ+c2stdmMtM0FDMEMxMTNCRkFEQzMxMzwvdGV4dD48L3VpZD4K
IDx4LWtvbGFiLXZlcnNpb24+PHRleHQ+My4wZGV2MTwvdGV4dD48L3gta29sYWItdmVyc2lv
bj4KIDxwcm9kaWQ+PHRleHQ+U3luY0tvbGFiIDMuMC4wLCBLb2xhYiByZXNvdXJjZTwvdGV4
dD48L3Byb2RpZD4KIDxyZXY+PHRpbWVzdGFtcD4xOTY5MTIzMVQwMDAwMDBaWjwvdGltZXN0
YW1wPjwvcmV2PgogPGtpbmQ+PHRleHQ+aW5kaXZpZHVhbDwvdGV4dD48L2tpbmQ+CiAgPGZu
Pjx0ZXh0Pkplcm9lbiB2YW4gTWVldXdlbjwvdGV4dD48L2ZuPgogPG4+CiAgIDxzdXJuYW1l
PnZhbiBNZWV1d2VuPC9zdXJuYW1lPgogICA8Z2l2ZW4+SmVyb2VuPC9naXZlbj4KIDwvbj4K
IDxuaWNrbmFtZT4KICAgIDx0ZXh0PmthbmFyaXA8L3RleHQ+CiA8L25pY2tuYW1lPgogPGVt
YWlsPgogIDxwYXJhbWV0ZXJzPjxwcmVmPjxpbnRlZ2VyPjE8L2ludGVnZXI+PC9wcmVmPjwv
cGFyYW1ldGVycz4KICA8dGV4dD5rYW5hcmlwQGthbmFyaXAuY29tPC90ZXh0PgogPC9lbWFp
bD4KPHgtY3VzdG9tPjxpZGVudGlmaWVyPlgtUHJlZmVyTWFpbEZvcm1hdDwvaWRlbnRpZmll
cj48dmFsdWU+dW5rbm93bjwvdmFsdWU+PC94LWN1c3RvbT4KIDx4LWN1c3RvbT48aWRlbnRp
Zmllcj5YLUFsbG93UmVtb3RlQ29udGVudDwvaWRlbnRpZmllcj48dmFsdWU+ZmFsc2U8L3Zh
bHVlPjwveC1jdXN0b20+CjwvdmNhcmQ+CjwvdmNhcmRzPgo=
--Boundary-00=363B189F14E3799C--
"""
        message = message_from_string(msg)

if __name__ == '__main__':
    unittest.main()
