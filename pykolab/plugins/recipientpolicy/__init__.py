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

import pykolab

from pykolab import utils
from pykolab.translate import _

conf = pykolab.getConf()
log = pykolab.getLogger('pykolab.plugins.recipientpolicy')

class KolabRecipientpolicy(object):
    """
        Example plugin making quota adjustments given arbitrary conditions.
    """

    def __init__(self):
        pass

    def add_options(self, *args,  **kw):
        pass

    #def mail_domain_space_policy_check(self, kw={}, args=()):
        #(mail, alternative_mail, domain_name, domain_root_dn) = args

        ## Your actions go here. For example:
        #return (mail, alternative_mail)

    def set_primary_mail(self, *args, **kw):
        """
            The arguments passed to the 'set_user_attrs_mail' hook:

            primary_mail - the policy
            user_attrs - the current user attributes
            primary_domain - the domain to use in the primary mail attribute
            secondary_domains - the secondary domains that are aliases

            Return the new primary mail address
        """

        user_attrs = utils.normalize(kw['entry'])

        if not user_attrs.has_key('domain'):
            user_attrs['domain'] = kw['primary_domain']
        elif not user_attrs['domain'] == kw['primary_domain']:
            user_attrs['domain'] = kw['primary_domain']

        try:
            mail = kw['primary_mail'] % user_attrs
            mail = utils.translate(mail, user_attrs['preferredlanguage'])
            mail = mail.lower()
            return mail
        except KeyError, e:
            log.warning(_("Attribute substitution for 'mail' failed in Recipient Policy"))
            mail = utils.translate(user_attrs['mail'], user_attrs['preferredlanguage'])
            mail = mail.lower()
            return mail

    def set_secondary_mail(self, *args, **kw):
        """
            The arguments passed to the 'set_user_attrs_alternative_mail' hook:

            primary_mail - the policy
            user_attrs - the current user attributes
            primary_domain - the domain to use in the primary mail attribute
            secondary_domains - the secondary domains that are aliases

            Return a list of secondary mail addresses
        """

        user_attrs = utils.normalize(kw['entry'])

        if not user_attrs.has_key('domain'):
            user_attrs['domain'] = kw['primary_domain']
        elif not user_attrs['domain'] == kw['primary_domain']:
            user_attrs['domain'] = kw['primary_domain']

        try:
            exec("alternative_mail_routines = %s" % kw['secondary_mail'])
        except Exception, e:
            log.error(_("Could not parse the alternative mail routines"))

        alternative_mail = []

        #print "%r" % (alternative_mail_routines)
        _domains = [ kw['primary_domain'] ] + kw['secondary_domains']

        for number in alternative_mail_routines.keys():
            for routine in alternative_mail_routines[number].keys():
                try:
                    exec("retval = '%s'.%s" % (routine,alternative_mail_routines[number][routine] % user_attrs))
                except KeyError, e:
                    log.warning(_("Attribute substitution for 'alternative_mail' failed in Recipient Policy"))

                #log.debug(_("Appending additional mail address: %s") % (retval), level=8)
                alternative_mail.append(utils.translate(retval, user_attrs['preferredlanguage']))

                for _domain in kw['secondary_domains']:
                    user_attrs['domain'] = _domain
                    try:
                        exec("retval = '%s'.%s" % (routine,alternative_mail_routines[number][routine] % user_attrs))
                    except KeyError, e:
                        log.warning(_("Attribute substitution for 'alternative_mail' failed in Recipient Policy"))

                    #log.debug(_("Appending additional mail address: %s") % (retval), level=8)
                    alternative_mail.append(utils.translate(retval, user_attrs['preferredlanguage']))

        alternative_mail = utils.normalize(alternative_mail)

        alternative_mail = list(set(alternative_mail))

        return alternative_mail
