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

import logging
import os
import time

import pykolab
import pykolab.base

from pykolab.translate import _

log = pykolab.getLogger('pykolab.auth')
conf = pykolab.getConf()

class Auth(pykolab.base.Base):
    """
        This is the Authentication and Authorization module for PyKolab.
    """

    def __init__(self, domain=None):
        """
            Initialize the authentication class.
        """
        pykolab.base.Base.__init__(self)

        self._auth = None

        if not domain == None:
            self.domain = domain
        else:
            self.domain = conf.get('kolab', 'primary_domain')

    def authenticate(self, login):
        """
            Verify login credentials supplied in login against the appropriate
            authentication backend.

            Login is a simple list of username, password, service and,
            optionally, the realm.
        """

        if len(login) == 3:
            # The realm has not been specified. See if we know whether or not
            # to use virtual_domains, as this may be a cause for the realm not
            # having been specified seperately.
            use_virtual_domains = conf.get('imap', 'virtual_domains')

            # TODO: Insert debug statements
            #if use_virtual_domains == "userid":
                #print "# Derive domain from login[0]"
            #elif not use_virtual_domains:
                #print "# Explicitly do not user virtual domains??"
            #else:
                ## Do use virtual domains, derive domain from login[0]
                #print "# Derive domain from login[0]"

        if len(login[0].split('@')) > 1:
            domain = login[0].split('@')[1]
        elif len(login) >= 4:
            domain = login[3]
        else:
            domain = conf.get("kolab", "primary_domain")

        # realm overrides domain
        if len(login) == 4:
            domain = login[3]

        retval = self._auth.authenticate(login, domain)

        return retval

    def connect(self, domain=None):
        """
            Connect to the domain authentication backend using domain, or fall
            back to the primary domain specified by the configuration.
        """

        log.debug(_("Called for domain %r") % (domain), level=9)

        if not self._auth == None:
            return

        if domain == None:
            section = 'kolab'
            domain = conf.get('kolab', 'primary_domain')
        else:
            self.list_domains()
            section = domain

        log.debug(
                _("Using section %s and domain %s") % (section,domain),
                level=9
            )

        if self.secondary_domains.has_key(domain):
            section = self.secondary_domains[domain]
            domain = self.secondary_domains[domain]

        log.debug(
                _("Using section %s and domain %s") % (section,domain),
                level=9
            )

        log.debug(
                _("Connecting to Authentication backend for domain %s") % (
                        domain
                    ),
                level=8
            )

        if not conf.has_section(section):
            section = 'kolab'

        if not conf.has_option(section, 'auth_mechanism'):
            log.debug(
                    _("Section %s has no option 'auth_mechanism'") % (section),
                    level=9
                )

            section = 'kolab'
        else:
            log.debug(
                    _("Section %s has auth_mechanism: %r") % (
                            section,
                            conf.get(section,'auth_mechanism')
                        ),
                    level=9
                )

        # Get the actual authentication and authorization backend.
        if conf.get(section, 'auth_mechanism') == 'ldap':
            log.debug(_("Starting LDAP..."), level=9)
            from pykolab.auth import ldap
            self._auth = ldap.LDAP(self.domain)

        elif conf.get(section, 'auth_mechanism') == 'sql':
            from pykolab.auth import sql
            self._auth = sql.SQL(self.domain)

        else:
            log.debug(_("Starting LDAP..."), level=9)
            from pykolab.auth import ldap
            self._auth = ldap.LDAP(self.domain)

        self._auth.connect()

    def disconnect(self):
        """
            Connect to the domain authentication backend using domain, or fall
            back to the primary domain specified by the configuration.
        """

        if domain == None:
            section = 'kolab'
            domain = conf.get('kolab', 'primary_domain')
        else:
            section = domain

        if not self._auth or self._auth == None:
            return

        self._auth._disconnect()

    def find_recipient(self, address, domain=None):
        """
            Find one or more entries corresponding to the recipient address.
        """
        if not domain == None:
            self.connect(domain=domain)

        result = self._auth.find_recipient(address)

        if isinstance(result, list) and len(result) == 1:
            return result[0]
        else:
            return result

    def find_resource(self, address):
        """
            Find one or more resources corresponding to the recipient address.
        """
        result = self._auth.find_resource(address)

        if isinstance(result, list) and len(result) == 1:
            return result[0]
        else:
            return result

    def find_user(self, attr, value, **kw):
        return self._auth._find_user(attr, value, **kw)

    def list_domains(self):
        """
            List the domains using the auth_mechanism setting in the kolab
            section of the configuration file, either ldap or sql or (...).

            The actual setting would be used by self.connect(), and stuffed
            into self._auth, for use with self._auth._list_domains()

            For each domain found, returns a two-part tuple of the primary
            domain and a list of secondary domains (aliases).
        """

        # Connect to the global namespace
        self.connect()

        # Find the domains in the authentication backend.
        kolab_primary_domain = conf.get('kolab', 'primary_domain')

        try:
            domains = self._auth._list_domains()
        except:
            if not self.domain == kolab_primary_domain:
                return [(self.domain, [])]

        # If no domains are found, the primary domain is used.
        if len(domains) < 1:
            domains = [(kolab_primary_domain, [])]
        else:
            for primary, secondaries in domains:
                for secondary in secondaries:
                    self.secondary_domains[secondary] = primary

        return domains

    def synchronize(self):
        self._auth.synchronize()

    def domain_default_quota(self, domain):
        return self._auth._domain_default_quota(domain)

    def get_entry_attribute(self, domain, entry, attribute):
        return self._auth.get_entry_attribute(entry, attribute)

    def get_entry_attributes(self, domain, entry, attributes):
        return self._auth.get_entry_attributes(entry, attributes)

    def get_user_attribute(self, domain, user, attribute):
        return self._auth.get_entry_attribute(user, attribute)

    def get_user_attributes(self, domain, user, attributes):
        return self._auth.get_entry_attributes(user, attributes)

    def search_entry_by_attribute(self, attr, value, **kw):
        return self._auth.search_entry_by_attribute(attr, value, **kw)

    def search_mail_address(self, domain, mail_address):
        return self._auth._search_mail_address(domain, mail_address)

    def set_entry_attribute(self, domain, entry, attribute):
        return self._auth.set_entry_attribute(entry, attribute)

    def set_entry_attributes(self, domain, entry, attributes):
        return self._auth.set_entry_attributes(entry, attributes)

    def set_user_attribute(self, domain, user, attribute, value):
        self._auth._set_user_attribute(user, attribute, value)
