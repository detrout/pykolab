# -*- coding: utf-8 -*-
#
# Cyruslib v0.8.5-20090401
# Copyright (C) 2007-2009 Reinaldo de Carvalho <reinaldoc@gmail.com>
# Copyright (C) 2003-2006 Gianluigi Tiesi <sherpya@netfarm.it>
# Copyright (C) 2003-2006 NetFarm S.r.l. [http://www.netfarm.it]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.
#
# Requires python >= 2.3
#

__version__ = '0.8.5'
__all__ = [ 'CYRUS' ]
__doc__ = """Cyrus admin wrapper
Adds cyrus-specific commands to imaplib IMAP4 Class
and defines new CYRUS class for cyrus imapd commands

"""

from sys import exit, stdout

try:
    import imaplib
    import re
    from binascii import b2a_base64
except ImportError, e:
    print e
    exit(1)

Commands = {
        'RECONSTRUCT'  : ('AUTH',),
        'DUMP'         : ('AUTH',), # To check admin status
        'ID'           : ('AUTH',), # Only one ID allowed in non auth mode
        'GETANNOTATION': ('AUTH',),
        'SETANNOTATION': ('AUTH',),
        'XFER'         : ('AUTH',)
    }

imaplib.Commands.update(Commands)

DEFAULT_SEP = '.'
QUOTE       = '"'
DQUOTE      = '""'

re_ns  = re.compile(r'.*\(\(\".*(\.|/)\"\)\).*')
re_q0  = re.compile(r'(.*)\s\(\)')
re_q   = re.compile(r'(.*)\s\(STORAGE (\d+) (\d+)\)')
re_mb  = re.compile(r'\((.*)\)\s\".\"\s(.*)')
re_url = re.compile(r'^(imaps?)://(.+?):?(\d{0,5})$')

def ok(res):
    return res.upper().startswith('OK')

def quote(text, qchar=QUOTE):
    return text.join([qchar, qchar])

def unquote(text, qchar=QUOTE):
    return ''.join(text.split(qchar))

def getflags(test):
    flags = []
    for flag in test.split('\\'):
        flag = flag.strip()
        if len(flag): flags.append(flag)
    return flags

### A smart function to return an array of splitted strings
### and honours quoted strings
def splitquote(text):
    data = text.split(QUOTE)
    if len(data) == 1: # no quotes
        res = data[0].split()
    else:
        res = []
        for match in data:
            if len(match.strip()) == 0: continue
            if match[0] == ' ':
                res = res + match.strip().split()
            else:
                res.append(match)
    return res

### return a dictionary from a cyrus info response
def res2dict(data):
    data = splitquote(data)
    datalen = len(data)
    if datalen % 2: # Unmatched pair
        return False, {}
    res = {}
    for i in range(0, datalen, 2):
        res[data[i]] = data[i+1]
    return True, res


class CYRUSError(Exception): pass

class IMAP4(imaplib.IMAP4):
    def getsep(self):
        """Get mailbox separator"""
        ### yes, ugly but cyradm does it in the same way
        ### also more realable then calling NAMESPACE
        ### and it should be also compatibile with other servers
        try:
            return unquote(self.list(DQUOTE, DQUOTE)[1][0]).split()[1]
        except:
            return DEFAULT_SEP

    def isadmin(self):
        ### A trick to check if the user is admin or not
        ### normal users cannot use dump command
        try:
            res, msg = self._simple_command('DUMP', 'NIL')
            if msg[0].lower().find('denied') == -1:
                return True
        except:
            pass
        return False

    def id(self):
        try:
            typ, dat = self._simple_command('ID', 'NIL')
            res, dat = self._untagged_response(typ, dat, 'ID')
        except:
            return False, dat[0]
        return ok(res), dat[0]

    def getannotation(self, mailbox, pattern='*', shared=None):
        if shared == None:
            typ, dat = self._simple_command('GETANNOTATION', mailbox, quote(pattern), quote('*'))
        elif shared:
            typ, dat = self._simple_command('GETANNOTATION', mailbox, quote(pattern), quote('value.shared'))
        else:
            typ, dat = self._simple_command('GETANNOTATION', mailbox, quote(pattern), quote('value.priv'))

        return self._untagged_response(typ, dat, 'ANNOTATION')

    def setannotation(self, mailbox, desc, value, shared=False):
        if value:
            value = quote(value)
        else:
            value = "NIL"
        if shared:
            typ, dat = self._simple_command('SETANNOTATION', mailbox, quote(desc), "(%s %s)" % (quote('value.shared'), value) )
        else:
            typ, dat = self._simple_command('SETANNOTATION', mailbox, quote(desc), "(%s %s)" % (quote('value.priv'), value) )

        return self._untagged_response(typ, dat, 'ANNOTATION')

    def setquota(self, mailbox, limit):
        """Set quota of a mailbox"""
        if limit == 0:
            quota = '()'
        else:
            quota = '(STORAGE %s)' % limit
        return self._simple_command('SETQUOTA', mailbox, quota)

    ### Overridden to support partition
    ### Pychecker will complain about non matching signature
    def create(self, mailbox, partition=None):
        """Create a mailbox, partition is optional"""
        if partition is not None:
            return self._simple_command('CREATE', mailbox, partition)
        else:
            return self._simple_command('CREATE', mailbox)

    ### Overridden to support partition
    ### Pychecker: same here
    def rename(self, from_mailbox, to_mailbox, partition=None):
        """Rename a from_mailbox to to_mailbox, partition is optional"""
        if partition is not None:
            return self._simple_command('RENAME', from_mailbox, to_mailbox, partition)
        else:
            return self._simple_command('RENAME', from_mailbox, to_mailbox)

    def reconstruct(self, mailbox):
        return self._simple_command('RECONSTRUCT', mailbox)

class IMAP4_SSL(imaplib.IMAP4_SSL):
    def getsep(self):
        """Get mailbox separator"""
        ### yes, ugly but cyradm does it in the same way
        ### also more realable then calling NAMESPACE
        ### and it should be also compatibile with other servers
        try:
            return unquote(self.list(DQUOTE, DQUOTE)[1][0]).split()[1]
        except:
            return DEFAULT_SEP

    def isadmin(self):
        ### A trick to check if the user is admin or not
        ### normal users cannot use dump command
        try:
            res, msg = self._simple_command('DUMP', 'NIL')
            if msg[0].lower().find('denied') == -1:
                return True
        except:
            pass
        return False

    def id(self):
        try:
            typ, dat = self._simple_command('ID', 'NIL')
            res, dat = self._untagged_response(typ, dat, 'ID')
        except:
            return False, dat[0]
        return ok(res), dat[0]

    def getannotation(self, mailbox, pattern='*', shared=None):
        if shared == None:
            typ, dat = self._simple_command('GETANNOTATION', mailbox, quote(pattern), quote('*'))
        elif shared:
            typ, dat = self._simple_command('GETANNOTATION', mailbox, quote(pattern), quote('value.shared'))
        else:
            typ, dat = self._simple_command('GETANNOTATION', mailbox, quote(pattern), quote('value.priv'))

        return self._untagged_response(typ, dat, 'ANNOTATION')

    def setannotation(self, mailbox, desc, value, shared=False):
        if value:
            value = quote(value)
        else:
            value = "NIL"
        if shared:
            typ, dat = self._simple_command('SETANNOTATION', mailbox, quote(desc), "(%s %s)" % (quote('value.shared'), value) )
        else:
            typ, dat = self._simple_command('SETANNOTATION', mailbox, quote(desc), "(%s %s)" % (quote('value.priv'), value) )

        return self._untagged_response(typ, dat, 'ANNOTATION')

    def setquota(self, mailbox, limit):
        """Set quota of a mailbox"""
        if limit == 0:
            quota = '()'
        else:
            quota = '(STORAGE %s)' % limit
        return self._simple_command('SETQUOTA', mailbox, quota)

    ### Overridden to support partition
    ### Pychecker will complain about non matching signature
    def create(self, mailbox, partition=None):
        """Create a mailbox, partition is optional"""
        if partition is not None:
            return self._simple_command('CREATE', mailbox, partition)
        else:
            return self._simple_command('CREATE', mailbox)

    ### Overridden to support partition
    ### Pychecker: same here
    def rename(self, from_mailbox, to_mailbox, partition=None):
        """Rename a from_mailbox to to_mailbox, partition is optional"""
        if partition is not None:
            return self._simple_command('RENAME', from_mailbox, to_mailbox, partition)
        else:
            return self._simple_command('RENAME', from_mailbox, to_mailbox)

    def reconstruct(self, mailbox):
        return self._simple_command('RECONSTRUCT', mailbox)

    def login_plain(self, admin, password, asUser):
        if asUser:
            encoded = b2a_base64("%s\0%s\0%s" % (asUser, admin, password)).strip()
        else:
            encoded = b2a_base64("%s\0%s\0%s" % (admin, admin, password)).strip()

        res, data = self._simple_command('AUTHENTICATE', 'PLAIN', encoded)
        if ok(res):
            self.state = 'AUTH'
        return res, data


class CYRUS:
    ERROR = {}
    ERROR["CONNECT"]     = [0,  "Connection error"]
    ERROR["INVALID_URL"] = [1,  "Invalid URL"]
    ERROR["ENCODING"]    = [3,  "Invalid encondig"]
    ERROR["MBXNULL"]     = [5,  "Mailbox is Null"]
    ERROR["NOAUTH"]      = [7,  "Connection is not authenticated"]
    ERROR["LOGIN"]       = [10, "User or password is wrong"]
    ERROR["ADMIN"]       = [11, "User is not cyrus administrator"]
    ERROR["AUTH"]        = [12, "Connection already authenticated"]
    ERROR["LOGINPLAIN"]  = [15, "Encryption needed to use mechanism"]
    ERROR["LOGIN_PLAIN"] = [16, "User or password is wrong"]
    ERROR["CREATE"]      = [20, "Unable create mailbox"]
    ERROR["DELETE"]      = [25, "Unable delete mailbox"]
    ERROR["GETACL"]      = [30, "Unable parse GETACL result"]
    ERROR["SETQUOTA"]    = [40, "Invalid integer argument"]
    ERROR["GETQUOTA"]    = [45, "Quota root does not exist"]
    ERROR["RENAME"]      = [50, "Unable rename mailbox"]
    ERROR["RECONSTRUCT"] = [60, "Unable reconstruct mailbox"]
    ERROR["SUBSCRIBE"]   = [70, "User is cyrus administrator, normal user required"]
    ERROR["UNSUBSCRIBE"] = [75, "User is cyrus administrator, normal user required"]
    ERROR["LSUB"]        = [77, "User is cyrus administrator, normal user required"]
    ERROR["UNKCMD"]      = [98, "Command not implemented"]
    ERROR["IMAPLIB"]     = [99, "Generic imaplib error"]

    ENCODING_LIST = ['imap', 'utf-8', 'iso-8859-1']

    def __init__(self, url = 'imap://localhost:143'):
        self.VERBOSE = False
        self.AUTH = False
        self.ADMIN = None
        self.AUSER = None
        self.ADMINACL = 'c'
        self.SEP = DEFAULT_SEP
        self.ENCODING = 'imap'
        self.LOGFD = stdout
        match = re_url.match(url)
        if match:
            host = match.group(2)
            if match.group(3):
                port = int(match.group(3))
            else:
                port = 143
        else:
            self.__doraise("INVALID_URL")
        try:
            if match.group(1) == 'imap':
                self.ssl = False
                self.m = IMAP4(host, port)
            else:
                self.ssl = True
                self.m = IMAP4_SSL(host, port)
        except:
            self.__doraise("CONNECT")

    def __del__(self):
        if self.AUTH:
            self.logout()

    def __verbose(self, msg):
        if self.VERBOSE:
            print >> self.LOGFD, msg

    def __doexception(self, function, msg=None, *args):
        if msg is None:
            try:
                msg = self.ERROR.get(function.upper())[1]
            except:
                msg = self.ERROR.get("IMAPLIB")[1]
        value = ""
        for arg in args:
            if arg is not None:
                value = "%s %s" % (value, arg)

        self.__verbose( '[%s%s] %s: %s' % (function.upper(), value, "BAD", msg) )
        self.__doraise( function.upper(), msg )

    def __doraise(self, mode, msg=None):
        idError = self.ERROR.get(mode)
        if idError:
            if msg is None:
                msg = idError[1]
        else:
            idError = [self.ERROR.get("IMAPLIB")[0]]
        raise CYRUSError( idError[0], mode, msg )


    def __prepare(self, command, mailbox=True):
        if not self.AUTH:
            self.__doexception(command, self.ERROR.get("NOAUTH")[1])
        elif not mailbox:
            self.__doexception(command, self.ERROR.get("MBXNULL")[1])

    def __docommand(self, function, *args):
        wrapped = getattr(self.m, function, None)
        if wrapped is None:
            raise self.__doraise("UNKCMD")
        try:
            res, msg = wrapped(*args)
            if ok(res):
                return res, msg
        except Exception, info:
            error = info.args[0].split(':').pop().strip()
            if error.upper().startswith('BAD'):
                error = error.split('BAD', 1).pop().strip()
                error = unquote(error[1:-1], '\'')
            self.__doexception(function, error, *args)
        self.__doexception(function, msg[0], *args)

    def xfer(self, mailbox, server):
        """Xfer a mailbox to server"""
        return self.m._simple_command('XFER', mailbox, server)

    def id(self):
        self.__prepare('id')
        res, data = self.m.id()
        data = data.strip()
        if not res or (len(data) < 3): return False, {}
        data = data[1:-1] # Strip ()
        res, rdata = res2dict(data)
        if not res:
            self.__verbose( '[ID] Umatched pairs in result' )
        return res, rdata

    def login(self, username, password):
        if self.AUTH:
            self.__doexception("LOGIN", self.ERROR.get("AUTH")[1])
        try:
            res, msg = self.m.login(username, password)
            admin = self.m.isadmin()
        except Exception, info:
            error = info.args[0].split(':').pop().strip()
            self.__doexception("LOGIN", error)

        if admin:
            self.ADMIN = username

        self.SEP = self.m.getsep()
        self.AUTH = True
        self.__verbose( '[LOGIN %s] %s: %s' % (username, res, msg[0]) )

    def login_plain(self, username, password, asUser = None):
        if self.AUTH:
            self.__doexception("LOGINPLAIN", self.ERROR.get("AUTH")[1])
        if not self.ssl:
            self.__doexception("LOGINPLAIN", self.ERROR.get("LOGINPLAIN")[1])
        res, msg = self.__docommand("login_plain", username, password, asUser)
        self.__verbose( '[AUTHENTICATE PLAIN %s] %s: %s' % (username, res, msg[0]) )

        if ok(res):
            if asUser is None:
                if self.m.isadmin():
                    self.ADMIN = admin
            else:
                self.ADMIN = asUser
                self.AUSER = asUser
            self.SEP = self.m.getsep()
            self.AUTH = True

    def logout(self):
        try:
            res, msg = self.m.logout()
        except Exception, info:
            error = info.args[0].split(':').pop().strip()
            self.__doexception("LOGOUT", error)
        self.AUTH = False
        self.ADMIN = None
        self.AUSER = None
        self.__verbose( '[LOGOUT] %s: %s' % (res, msg[0]) )

    def getEncoding(self):
        """Get current input/ouput codification"""
        return self.ENCODING

    def setEncoding(self, enc = None):
        """Set current input/ouput codification"""
        if enc is None:
            self.ENCODING = 'imap'
        elif enc in self.ENCODING_LIST:
            self.ENCODING = enc
        else:
            raise self.__doraise("ENCODING")

    def __encode(self, text):
        if re.search("&", text):
            text = re.sub("/", "+AC8-", text)
            text = re.sub("&", "+", text)
            text = unicode(text, 'utf-7').encode(self.ENCODING)
        return text

    def encode(self, text):
        if self.ENCODING == 'imap':
            return text
        elif self.ENCODING in self.ENCODING_LIST:
            return self.__encode(text)

    def __decode(self, text):
        text = re.sub("/", "-&", text)
        text = re.sub(" ", "-@", text)
        text = unicode(text, self.ENCODING).encode('utf-7')
        text = re.sub("-@", " ", text)
        text = re.sub("-&", "/", text)
        text = re.sub("\+", "&", text)
        return text

    def decode(self, text):
        if self.ENCODING == 'imap':
            return text
        elif self.ENCODING in self.ENCODING_LIST:
            return self.__decode(text)

    def lm(self, pattern="*"):
        """
        List mailboxes, returns dict with list of mailboxes

        To list all mailboxes                       lm()
        To list users top mailboxes                 lm("user/%")
        To list all users mailboxes                 lm("user/*")
        To list users mailboxes startwith a word    lm("user/word*")
        To list global top folders                  lm("%")
        To list global startwith a word             unsupported by server
          suggestion                                lm("word*")

        """
        self.__prepare('LIST')
        if pattern == '': pattern = "*"
        if pattern == '%':
            res, ml = self.__docommand('list', '', '%')
        else:
            res, ml = self.__docommand('list', '""', self.decode(pattern))

        if not ok(res):
            self.__verbose( '[LIST] %s: %s' % (res, ml) )
            return []

        if (len(ml) == 1) and ml[0] is None:
            self.__verbose( '[LIST] No results' )
            return []

        mb = []
        for mailbox in ml:
            res = re_mb.match(mailbox)
            if res is None: continue
            mbe = unquote(res.group(2))
            if 'Noselect' in getflags(res.group(1)): continue
            mb.append(self.encode(mbe))
        return mb

    def cm(self, mailbox, partition=None):
        """Create mailbox"""
        self.__prepare('CREATE', mailbox)
        res, msg = self.__docommand('create', self.decode(mailbox), partition)
        self.__verbose( '[CREATE %s partition=%s] %s: %s' % (mailbox, partition, res, msg[0]) )

    def __dm(self, mailbox):
        if not mailbox:
            return True
        self.__docommand("setacl", self.decode(mailbox), self.ADMIN, self.ADMINACL)
        res, msg = self.__docommand("delete", self.decode(mailbox))
        self.__verbose( '[DELETE %s] %s: %s' % (mailbox, res, msg[0]) )

    def dm(self, mailbox, recursive=True):
        """Delete mailbox"""
        self.__prepare('DELETE', mailbox)
        mbxTmp = mailbox.split(self.SEP)
        # Cyrus is not recursive for user subfolders and global folders
        if (recursive and mbxTmp[0] != "user") or (len(mbxTmp) > 2):
            mbxList = self.lm("%s%s*" % (mailbox, self.SEP))
            mbxList.reverse()
            for mbox in mbxList:
                self.__dm(mbox)
        self.__dm(mailbox)

    def rename(self, fromMbx, toMbx, partition=None):
        """Rename or change partition"""
        self.__prepare('RENAME', fromMbx)
        # Rename is recursive! Amen!
        res, msg = self.__docommand("rename", self.decode(fromMbx), self.decode(toMbx), partition)
        self.__verbose( '[RENAME %s %s] %s: %s' % (fromMbx, toMbx, res, msg[0]) )

    def lam(self, mailbox):
        """List ACLs"""
        self.__prepare('GETACL', mailbox)
        res, acl = self.__docommand("getacl", self.decode(mailbox))
        acls = {}
        aclList = splitquote(acl.pop().strip())
        del aclList[0] # mailbox
        for i in range(0, len(aclList), 2):
            try:
                userid = self.encode(aclList[i])
                rights = aclList[i + 1]
            except Exception, info:
                self.__verbose( '[GETACL %s] BAD: %s' % (mailbox, info.args[0]) )
                raise self.__doraise("GETACL")
            self.__verbose( '[GETACL %s] %s %s' % (mailbox, userid, rights) )
            acls[userid] = rights
        return acls

    def sam(self, mailbox, userid, rights):
        """Set ACL"""
        self.__prepare('SETACL', mailbox)
        res, msg = self.__docommand("setacl", self.decode(mailbox), userid, rights)
        self.__verbose( '[SETACL %s %s %s] %s: %s' % (mailbox, userid, rights, res, msg[0]) )

    def lq(self, mailbox):
        """List Quota"""
        self.__prepare('GETQUOTA', mailbox)
        res, msg = self.__docommand("getquota", self.decode(mailbox))
        match = re_q0.match(msg[0])
        if match:
            self.__verbose( '[GETQUOTA %s] QUOTA (Unlimited)' % mailbox )
            return None, None
        match = re_q.match(msg[0])
        if match is None:
            self.__verbose( '[GETQUOTA %s] BAD: RegExp not matched, please report' % mailbox )
            return None, None
        try:
            used = int(match.group(2))
            quota = int(match.group(3))
            self.__verbose( '[GETQUOTA %s] %s: QUOTA (%d/%d)' % (mailbox, res, used, quota) )
            return used, quota
        except:
            self.__verbose( '[GETQUOTA %s] BAD: Error while parsing results' % mailbox )
            return None, None

    def lqr(self, mailbox):
        """List Quota Root"""
        self.__prepare('GETQUOTAROOT', mailbox)
        res, msg = self.__docommand("getquotaroot", self.decode(mailbox))
        (_mailbox, _root) = msg[0][0].split()

        match = re_q0.match(msg[1][0])
        if match:
            self.__verbose( '[GETQUOTAROOT %s] QUOTAROOT (Unlimited)' % mailbox )
            return _root, None, None

        match = re_q.match(msg[1][0])
        try:
            used = int(match.group(2))
            quota = int(match.group(3))
            self.__verbose( '[GETQUOTAROOT %s] %s: QUOTA (%d/%d)' % (mailbox, res, used, quota) )
            return _root, used, quota
        except:
            self.__verbose( '[GETQUOTAROOT %s] BAD: Error while parsing results' % mailbox )
            return _root, None, None

    def sq(self, mailbox, limit):
        """Set Quota"""
        self.__prepare('SETQUOTA', mailbox)
        try:
            limit = int(limit)
        except ValueError, e:
            self.__verbose( '[SETQUOTA %s] BAD: %s %s' % (mailbox, self.ERROR.get("SETQUOTA")[1], limit) )
            raise self.__doraise("SETQUOTA")
        res, msg = self.__docommand("setquota", self.decode(mailbox), limit)
        self.__verbose( '[SETQUOTA %s %s] %s: %s' % (mailbox, limit, res, msg[0]) )

    def getannotation(self, mailbox, pattern='*'):
        """Get Annotation"""
        self.__prepare('GETANNOTATION')
        res, data = self.__docommand('getannotation', self.decode(mailbox), pattern)
        if (len(data) == 1) and data[0] is None:
            self.__verbose( '[GETANNOTATION %s] No results' % (mailbox) )
            return {}
        ann = {}

        annotations = []
        empty_values = [ "NIL", '" "', None, '', ' ' ]

        concat_items = []
        for item in data:
            if isinstance(item, tuple):
                item = ' '.join([str(x) for x in item])

            if len(concat_items) > 0:
                concat_items.append(item)

                if ''.join(concat_items).count('(') == ''.join(concat_items).count(')'):
                    annotations.append(''.join(concat_items))
                    concat_items = []
                    continue
            else:

                if item.count('(') == item.count(')'):
                    annotations.append(item)
                    continue
                else:
                    concat_items.append(item)
                    continue

        for annotation in annotations:

            folder = annotation.split()[0].replace('"','')

            if not ann.has_key(folder):
                ann[folder] = {}

            key = annotation.split()[1].replace('"','').replace("'","")

            _annot = annotation.split('(')[1].split(')')[0]

            try:
                value_priv = _annot[(_annot.index('"value.priv"')+len('"value.priv"')):_annot.index('"size.priv"')].strip()
            except ValueError, errmsg:
                value_priv = None

            try:
                size_priv = _annot[(_annot.index('"size.priv"')+len('"size.priv"')):].strip().split('"')[1].strip()
                try:
                    value_priv = value_priv[value_priv.index('{%s}' % (size_priv))+len('{%s}' % (size_priv)):].strip()
                except Exception, errmsg:
                    pass
            except Exception, errmsg:
                pass

            if value_priv in empty_values:
                value_priv = None
            else:
                try:
                    value_priv = value_priv[:value_priv.index('"content-type.priv"')].strip()
                except:
                    pass

                try:
                    value_priv = value_priv[:value_priv.index('"modifiedsince.priv"')].strip()
                except:
                    pass

                if value_priv.startswith('"'):
                    value_priv = value_priv[1:]

                if value_priv.endswith('"'):
                    value_priv = value_priv[:-1]

            if value_priv in empty_values:
                value_priv = None

            try:
                value_shared = _annot[(_annot.index('"value.shared"')+len('"value.shared"')):_annot.index('"size.shared"')].strip()
            except ValueError, errmsg:
                value_shared = None

            try:
                size_shared = _annot[(_annot.index('"size.shared"')+len('"size.shared"')):].strip().split('"')[1].strip()
                try:
                    value_shared = value_shared[value_shared.index('{%s}' % (size_shared))+len('{%s}' % (size_shared)):].strip()
                except Exception, errmsg:
                    pass
            except Exception, errmsg:
                pass

            if value_shared in empty_values:
                value_shared = None
            else:
                try:
                    value_shared = value_shared[:value_shared.index('"content-type.shared"')].strip()
                except:
                    pass

                try:
                    value_shared = value_shared[:value_shared.index('"modifiedsince.shared"')].strip()
                except:
                    pass

                if value_shared.startswith('"'):
                    value_shared = value_shared[1:]

                if value_shared.endswith('"'):
                    value_shared = value_shared[:-1]

            if value_shared in empty_values:
                value_shared = None

            if not value_priv == None:
                ann[folder]['/private' + key] = value_priv

            if not value_shared == None:
                ann[folder]['/shared' + key] = value_shared

        return ann

    def setannotation(self, mailbox, annotation, value, shared=False):
        """Set Annotation"""
        self.__prepare('SETANNOTATION')
        res, msg = self.__docommand("setannotation", self.decode(mailbox), annotation, value, shared)
        self.__verbose( '[SETANNOTATION %s] %s: %s' % (mailbox, res, msg[0]) )

    def __reconstruct(self, mailbox):
        if not mailbox:
            return True
        res, msg = self.__docommand("reconstruct", self.decode(mailbox))
        self.__verbose( '[RECONSTRUCT %s] %s: %s' % (mailbox, res, msg[0]) )

    def reconstruct(self, mailbox, recursive=True):
        """Reconstruct"""
        self.__prepare('RECONSTRUCT', mailbox)
        # Cyrus is not recursive for remote reconstruct
        if recursive:
            mbxList = self.lm("%s%s*" % (mailbox, self.SEP))
            mbxList.reverse()
            for mbox in mbxList:
                self.__reconstruct(mbox)
        self.__reconstruct(mailbox)

    def lsub(self, pattern="*"):
        if self.AUSER is None:
            self.__doexception("lsub")
        self.__prepare('LSUB')
        if pattern == '': pattern = "*"
        res, ml = self.__docommand('lsub', '*', pattern)

        if not ok(res):
            self.__verbose( '[LIST] %s: %s' % (res, ml) )
            return []

        if (len(ml) == 1) and ml[0] is None:
            self.__verbose( '[LIST] No results' )
            return []

        mb = []
        for mailbox in ml:
            res = re_mb.match(mailbox)
            if res is None: continue
            mbe = unquote(res.group(2))
            if 'Noselect' in getflags(res.group(1)): continue
            mb.append(self.encode(mbe))
        return mb

    def subscribe(self, mailbox):
        """Subscribe"""
        self.__prepare('SUBSCRIBE')
        res, msg = self.__docommand("subscribe", self.decode(mailbox))
        self.__verbose( '[SUBSCRIBE %s] %s: %s' % (mailbox, res, msg[0]) )

    def unsubscribe(self, mailbox):
        """Unsubscribe"""
        self.__prepare('UNSUBSCRIBE')
        res, msg = self.__docommand("unsubscribe", self.decode(mailbox))
        self.__verbose( '[UNSUBSCRIBE %s] %s: %s' % (mailbox, res, msg[0]) )

