# -*- coding: utf-8 -*-
# Copyright 2010-2012 Kolab Systems AG (http://www.kolabsys.com)
#
# Jeroen van Meeuwen (Kolab Systems) <vanmeeuwen a kolabsys.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 or, at your option, any later version
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

from Cheetah.Template import Template
import os
import subprocess

import components

import pykolab

from pykolab import utils
from pykolab.constants import *
from pykolab.translate import _

log = pykolab.getLogger('pykolab.setup')
conf = pykolab.getConf()

def __init__():
    components.register(
            'imap',
            execute,
            description=description(),
            after=['ldap']
        )

def description():
    return _("Setup IMAP.")

def execute(*args, **kw):
    """
        Apply the necessary settings to /etc/imapd.conf
    """

    imapd_settings = {
            "ldap_servers": conf.get('ldap', 'ldap_uri'),
            "ldap_base": conf.get('ldap', 'base_dn'),
            "ldap_bind_dn": conf.get('ldap', 'service_bind_dn'),
            "ldap_password": conf.get('ldap', 'service_bind_pw'),
            "ldap_filter": '(|(&(|(uid=%s)(uid=cyrus-murder))(uid=%%U))(&(|(uid=%%U)(mail=%%U@%%d)(mail=%%U@%%r))(objectclass=kolabinetorgperson)))' % (conf.get('cyrus-imap', 'admin_login')),
            "ldap_user_attribute": conf.get('cyrus-sasl', 'result_attribute'),
            "ldap_group_base": conf.get('ldap', 'base_dn'),
            "ldap_group_filter": "(&(cn=%u)(objectclass=ldapsubentry)(objectclass=nsroledefinition))",
            "ldap_group_scope": "one",
            "ldap_member_base": conf.get('ldap','user_base_dn'),
            "ldap_member_method": "attribute",
            "ldap_member_attribute": "nsrole",
            "admins": conf.get('cyrus-imap', 'admin_login'),
            "postuser": "shared",
        }

    template_file = None

    if os.path.isfile('/etc/kolab/templates/imapd.conf.tpl'):
        template_file = '/etc/kolab/templates/imapd.conf.tpl'
    elif os.path.isfile('/usr/share/kolab/templates/imapd.conf.tpl'):
        template_file = '/usr/share/kolab/templates/imapd.conf.tpl'
    elif os.path.isfile(os.path.abspath(os.path.join(__file__, '..', '..', '..', 'share', 'templates', 'imapd.conf.tpl'))):
        template_file = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'share', 'templates', 'imapd.conf.tpl'))

    if not template_file == None:
        fp = open(template_file, 'r')
        template_definition = fp.read()
        fp.close()

        t = Template(template_definition, searchList=[imapd_settings])
        fp = open('/etc/imapd.conf', 'w')
        fp.write(t.__str__())
        fp.close()

    else:
        log.error(_("Could not write out Cyrus IMAP configuration file /etc/imapd.conf"))
        return

    cyrus_settings = {}

    template_file = None

    if os.path.isfile('/etc/kolab/templates/cyrus.conf.tpl'):
        template_file = '/etc/kolab/templates/cyrus.conf.tpl'
    elif os.path.isfile('/usr/share/kolab/templates/cyrus.conf.tpl'):
        template_file = '/usr/share/kolab/templates/cyrus.conf.tpl'
    elif os.path.isfile(os.path.abspath(os.path.join(__file__, '..', '..', '..', 'share', 'templates', 'cyrus.conf.tpl'))):
        template_file = os.path.abspath(os.path.join(__file__, '..', '..', '..', 'share', 'templates', 'cyrus.conf.tpl'))

    if not template_file == None:
        fp = open(template_file, 'r')
        template_definition = fp.read()
        fp.close()

        t = Template(template_definition, searchList=[cyrus_settings])
        fp = open('/etc/cyrus.conf', 'w')
        fp.write(t.__str__())
        fp.close()

    else:
        log.error(_("Could not write out Cyrus IMAP configuration file /etc/imapd.conf"))
        return

    annotations = [
            "/vendor/horde/share-params,mailbox,string,backend,value.shared value.priv,a",
            "/vendor/kolab/color,mailbox,string,backend,value.shared value.priv,a",
            "/vendor/kolab/folder-test,mailbox,string,backend,value.shared value.priv,a",
            "/vendor/kolab/folder-type,mailbox,string,backend,value.shared value.priv,a",
            "/vendor/kolab/incidences-for,mailbox,string,backend,value.shared value.priv,a",
            "/vendor/kolab/pxfb-readable-for,mailbox,string,backend,value.shared value.priv,a",
            "/vendor/kolab/h-share-attr-desc,mailbox,string,backend,value.shared value.priv,a",
            "/vendor/kolab/activesync,mailbox,string,backend,value.priv,r",
            "/vendor/x-toltec/test,mailbox,string,backend,value.shared value.priv,a",
        ]

    fp = open('/etc/imapd.annotations.conf', 'w')
    fp.write("\n".join(annotations))
    fp.close()

    if os.path.isfile('/bin/systemctl'):
        subprocess.call(['systemctl', 'restart', 'cyrus-imapd.service'])
        subprocess.call(['systemctl', 'enable', 'cyrus-imapd.service'])
        subprocess.call(['systemctl', 'restart', 'kolab-saslauthd.service'])
        subprocess.call(['systemctl', 'enable', 'kolab-saslauthd.service'])
    elif os.path.isfile('/sbin/service'):
        subprocess.call(['service', 'cyrus-imapd', 'restart'])
        subprocess.call(['chkconfig', 'cyrus-imapd', 'on'])
        subprocess.call(['service', 'kolab-saslauthd', 'restart'])
        subprocess.call(['chkconfig', 'kolab-saslauthd', 'on'])
    else:
        log.error(_("Could not start and configure to start on boot, the " + \
                "cyrus-imapd and kolab-saslauthd services."))
