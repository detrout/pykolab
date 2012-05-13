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

"""
    The Kolab daemon.
"""

import os
import shutil
import sys
import time
import traceback

import pykolab

from pykolab.auth import Auth
from pykolab import constants
from pykolab.translate import _

from process import KolabdProcess as Process

log = pykolab.getLogger('pykolab.daemon')
conf = pykolab.getConf()

class KolabDaemon(object):
    def __init__(self):
        """
            The main Kolab Groupware daemon process.
        """

        daemon_group = conf.add_cli_parser_option_group(_("Daemon Options"))

        daemon_group.add_option(  "--fork",
                                dest    = "fork_mode",
                                action  = "store_true",
                                default = False,
                                help    = _("Fork to the background."))

        daemon_group.add_option( "-p", "--pid-file",
                                dest    = "pidfile",
                                action  = "store",
                                default = "/var/run/kolabd/kolabd.pid",
                                help    = _("Path to the PID file to use."))

        conf.finalize_conf()

    def run(self):
        """Run Forest, RUN!"""

        exitcode = 0

        try:
            pid = 1
            if conf.fork_mode:
                pid = os.fork()

            if pid == 0:
                log.remove_stdout_handler()
                self.write_pid()
                self.set_signal_handlers()
                self.do_sync()
            elif not conf.fork_mode:
                self.do_sync()

        except SystemExit, errcode:
            exitcode = errcode

        except KeyboardInterrupt:
            exitcode = 1
            log.info(_("Interrupted by user"))

        except AttributeError, errmsg:
            exitcode = 1
            traceback.print_exc()
            print >> sys.stderr, _("Traceback occurred, please report a " + \
                "bug at http://bugzilla.kolabsys.com")

        except TypeError, errmsg:
            exitcode = 1
            traceback.print_exc()
            log.error(_("Type Error: %s") % errmsg)

        except:
            exitcode = 2
            traceback.print_exc()
            print >> sys.stderr, _("Traceback occurred, please report a " + \
                "bug at http://bugzilla.kolabsys.com")

        sys.exit(exitcode)

    def do_sync(self):
        domain_auth = {}

        pid = os.getpid()

        primary_domain = conf.get('kolab', 'primary_domain')

        while 1:
            primary_auth = Auth(primary_domain)

            log.debug(_("Listing domains..."), level=5)

            start = time.time()

            try:
                domains = primary_auth.list_domains()
            except:
                time.sleep(60)
                continue

            # domains now is a list of tuples, we want the primary_domains
            primary_domains = []
            for primary_domain, secondary_domains in domains:
                primary_domains.append(primary_domain)

            # Now we can check if any changes happened.
            added_domains = []
            removed_domains = []

            all_domains = set(primary_domains + domain_auth.keys())

            for domain in all_domains:
                if domain in domain_auth.keys() and domain in primary_domains:
                    continue
                elif domain in domain_auth.keys():
                    removed_domains.append(domain)
                else:
                    added_domains.append(domain)

            if len(removed_domains) == 0 and len(added_domains) == 0:
                time.sleep(600)

            log.debug(_("added domains: %r, removed domains: %r") % (added_domains, removed_domains), level=8)

            for domain in added_domains:
                domain_auth[domain] = Process(domain)
                domain_auth[domain].start()

    def reload_config(self, *args, **kw):
        pass

    def remove_pid(self, *args, **kw):
        if os.access(conf.pidfile, os.R_OK):
            os.remove(conf.pidfile)
        raise SystemExit

    def set_signal_handlers(self):
        import signal
        signal.signal(signal.SIGHUP, self.reload_config)
        signal.signal(signal.SIGTERM, self.remove_pid)

    def write_pid(self):
        pid = os.getpid()
        fp = open(conf.pidfile,'w')
        fp.write("%d\n" % (pid))
        fp.close()
