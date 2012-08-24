
import json
import httplib
import sys
from urlparse import urlparse

import pykolab

from pykolab import utils
from pykolab.translate import _

log = pykolab.getLogger('pykolab.wap_client')
conf = pykolab.getConf()

if not hasattr(conf, 'defaults'):
    conf.finalize_conf()

API_HOSTNAME = "localhost"
API_SCHEME = "http"
API_PORT = 80
API_BASE = "/kolab-webadmin/api/"

kolab_wap_url = conf.get('kolab_wap', 'api_url')

if not kolab_wap_url == None:
    result = urlparse(kolab_wap_url)
else:
    result = None

if hasattr(result, 'hostname'):
    API_HOSTNAME = result.hostname

if hasattr(result, 'port'):
    API_PORT = result.port

if hasattr(result, 'path'):
    API_BASE = result.path

session_id = None

conn = None

from connect import connect

def authenticate(username=None, password=None, domain=None):
    global session_id

    conf_username = conf.get('ldap', 'service_bind_dn')
    conf_password = conf.get('ldap', 'service_bind_pw')

    if username == None:
        username = utils.ask_question("Login", default=conf_username)

    if username == conf_username:
        password = conf_password

    if username == conf.get('ldap', 'bind_dn'):
        password = conf.get('ldap', 'bind_pw')

    if password == None:
        password = utils.ask_question("Password", default=conf_password, password=True)

    if domain == None:
        domain = conf.get('kolab', 'primary_domain')

    params = json.dumps(
            {
                    'username': username,
                    'password': password,
                    'domain': domain
                }
        )

    response = request('POST', "system.authenticate", params)

    if response.has_key('session_token'):
        session_id = response['session_token']

def connect():
    global conn

    if conn == None:
        conn = httplib.HTTPConnection(API_HOSTNAME, API_PORT)
        conn.connect()

    return conn

def domain_add(domain, parent=None):
    params = {
            'domain': domain,
        }

    dna = conf.get('ldap', 'domain_name_attribute')

    if not parent == None:
        domains = domains_list()
        parent_found = False
        if isinstance(domains['list'], dict):
            for _domain in domains['list'].keys():
                if parent_found:
                    continue

                if isinstance(domains['list'][_domain][dna], basestring):
                    if parent == domains['list'][_domain][dna]:
                        parent_found = True
                elif isinstance(domains['list'][_domain][dna], list):
                    if parent in domains['list'][_domain][dna]:
                        parent_found = True

        if parent_found:
            params['parent'] = parent
        else:
            log.error(_("Invalid parent domain"))
            return

    params = json.dumps(params)

    return request('POST', 'domain.add', params)

def domain_info(domain):
    return request('GET', 'domain.info?domain=%s' % (domain))

def domains_capabilities():
    return request('GET', 'domains.capabilities')

def domains_list():
    return request('GET', 'domains.list')

def form_value_generate(params):
    params = json.dumps(params)

    return request('POST', 'form_value.generate', params)

def get_group_input():
    group_types = group_types_list()

    if len(group_types.keys()) > 1:
        for key in group_types.keys():
            if not key == "status":
                print "%s) %s" % (key,group_types[key]['name'])

        group_type_id = utils.ask_question("Please select the group type")

    elif len(group_types.keys()) > 0:
        print "Automatically selected the only group type available"
        group_type_id = group_types.keys()[0]

    else:
        print "No group types available"
        sys.exit(1)

    if group_types.has_key(group_type_id):
        group_type_info = group_types[group_type_id]['attributes']
    else:
        print "No such group type"
        sys.exit(1)

    params = {
            'group_type_id': group_type_id
        }

    for attribute in group_type_info['form_fields'].keys():
        params[attribute] = utils.ask_question(attribute)

    for attribute in group_type_info['auto_form_fields'].keys():
        exec("retval = group_form_value_generate_%s(params)" % (attribute))
        params[attribute] = retval[attribute]

    return params

def get_user_input():
    user_types = user_types_list()

    if user_types['count'] > 1:
        for key in user_types['list'].keys():
            if not key == "status":
                print "%s) %s" % (key,user_types['list'][key]['name'])

        user_type_id = utils.ask_question("Please select the user type")

    elif user_types['count'] > 0:
        print "Automatically selected the only user type available"
        user_type_id = user_types['list'].keys()[0]

    else:
        print "No user types available"
        sys.exit(1)

    if user_types['list'].has_key(user_type_id):
        user_type_info = user_types['list'][user_type_id]['attributes']
    else:
        print "No such user type"
        sys.exit(1)

    params = {
            'user_type_id': user_type_id
        }

    for attribute in user_type_info['form_fields'].keys():
        params[attribute] = utils.ask_question(attribute)

    for attribute in user_type_info['auto_form_fields'].keys():
        exec("retval = form_value_generate_%s(params)" % (attribute))
        params[attribute] = retval[attribute]

    return params

def group_add(params=None):
    if params == None:
        params = get_group_input()

    params = json.dumps(params)

    return request('POST', 'group.add', params)

def group_form_value_generate_mail(params=None):
    if params == None:
        params = get_user_input()

    params = json.dumps(params)

    return request('POST', 'group_form_value.generate_mail', params)

def group_info():
    group = utils.ask_question("Group email address")
    group = request('GET', 'group.info?group=%s' % (group))
    return group

def group_members_list(group=None):
    if group == None:
        group = utils.ask_question("Group email address")
    group = request('GET', 'group.members_list?group=%s' % (group))
    return group

def group_types_list():
    return request('GET', 'group_types.list')

def groups_list():
    return request('GET', 'groups.list')

def request(method, api_uri, params=None, headers={}):
    response_data = request_raw(method, api_uri, params, headers)

    if response_data['status'] == "OK":
        del response_data['status']
        return response_data['result']
    else:
        return response_data['result']

def request_raw(method, api_uri, params=None, headers={}):
    global session_id

    if not session_id == None:
        headers["X-Session-Token"] = session_id

    conn = connect()
    log.debug(_("Requesting %r with params %r") % ("%s/%s" % (API_BASE,api_uri), params), level=8)
    conn.request(method.upper(), "%s/%s" % (API_BASE,api_uri), params, headers)
    response = conn.getresponse()

    data = response.read()

    log.debug(_("Got response: %r") % (data), level=8)
    try:
        response_data = json.loads(data)
    except ValueError, e:
        # Some data is not JSON
        log.error(_("Response data is not JSON"))

    return response_data

def role_capabilities():
    return request('GET', 'role.capabilities')

def system_capabilities():
    return request('GET', 'system.capabilities')

def system_get_domain():
    return request('GET', 'system.get_domain')

def system_select_domain(domain=None):
    if domain == None:
        domain = utils.ask_question("Domain name")
    return request('GET', 'system.select_domain?domain=%s' % (domain))

def user_add(params=None):
    if params == None:
        params = get_user_input()

    params = json.dumps(params)

    return request('POST', 'user.add', params)

def user_delete(params=None):
    if params == None:
        params = {
                'user': utils.ask_question("Username for user to delete", "user")
            }

    params = json.dumps(params)

    return request('POST', 'user.delete', params)

def user_edit(params=None):
    if params == None:
        params = {
                'user': utils.ask_question("Username for user to edit", "user")
            }

    params = json.dumps(params)

    user = request('GET', 'user.info', params)

    return user

def user_form_value_generate_cn(params=None):
    if params == None:
        params = get_user_input()

    params = json.dumps(params)

    return request('POST', 'user_form_value.generate_cn', params)

def user_form_value_generate_displayname(params=None):
    if params == None:
        params = get_user_input()

    params = json.dumps(params)

    return request('POST', 'user_form_value.generate_displayname', params)

def user_form_value_generate_mail(params=None):
    if params == None:
        params = get_user_input()

    params = json.dumps(params)

    return request('POST', 'user_form_value.generate_mail', params)

def form_value_generate_password(*args, **kw):
    return request('GET', 'form_value.generate_password')

def form_value_list_options(attribute_name, *args, **kw):
    params = json.dumps({'attribute': attribute_name})

    return request('POST', 'form_value.list_options', params)

def form_value_select_options(attribute_name, *args, **kw):
    params = json.dumps({'attributes': [attribute_name]})

    return request('POST', 'form_value.select_options', params)

def role_find_by_attribute(params=None):
    if params == None:
        role_name = utils.ask_question("Role name")
    else:
        role_name = params['cn']

    role = request('GET', 'role.find_by_attribute?cn=%s' % (role_name))

    return role

def role_add(params=None):
    if params == None:
        role_name = utils.ask_question("Role name")
        params = {
                'cn': role_name
            }

    params = json.dumps(params)

    return request('POST', 'role.add', params)

def role_delete(params=None):
    if params == None:
        role_name = utils.ask_question("Role name")
        role = role_find_by_attribute({'cn': role_name})
        params = {
                'role': role.keys()[0]
            }

    if not params.has_key('role'):
        role = role_find_by_attribute(params)
        params = {
                'role': role.keys()[0]
            }

    params = json.dumps(params)

    return request('POST', 'role.delete', params)

def role_info(params=None):
    if params == None:
        role_name = utils.ask_question("Role name")
        role = role_find_by_attribute({'cn': role_name})
        params = {
                'role': role
            }

    if not params.has_key('role'):
        role = role_find_by_attribute(params)
        params = {
                'role': role
            }

    role = request('GET', 'role.info?role=%s' % (params['role'].keys()[0]))

    return role

def roles_list():
    return request('GET', 'roles.list')

def user_form_value_generate_uid(params=None):
    if params == None:
        params = get_user_input()

    params = json.dumps(params)

    return request('POST', 'user_form_value.generate_uid', params)

def user_form_value_generate_userpassword(*args, **kw):
    result = form_value_generate_password()
    return { 'userpassword': result['password'] }

def user_info(user=None):
    if user == None:
        user = utils.ask_question("User email address")
    user = request('GET', 'user.info?user=%s' % (user))
    return user

def user_types_list():
    return request('GET', 'user_types.list')

def users_list():
    return request('GET', 'users.list')

