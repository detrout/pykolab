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

import commands

import pykolab

from pykolab import utils
from pykolab.translate import _

log = pykolab.getLogger('pykolab.cli')
conf = pykolab.getConf()

def __init__():
    commands.register('user_info', execute, description="Display user information.")

def execute(*args, **kw):
    from pykolab import wap_client

    try:
        user = conf.cli_args.pop(0)
    except IndexError, errmsg:
        user = utils.ask_question(_("User"))

    # Create the authentication object.
    # TODO: Binds with superuser credentials!
    wap_client.authenticate(username=conf.get("ldap", "bind_dn"), password=conf.get("ldap", "bind_pw"))
    user = wap_client.user_info(user)

    print user

