from ckan.common import config, request
from ckanext.geoserver_webservice.model import GeoserverUserRoleModel
from ckanext.geoserver_webservice.model import GeoserverUserAuthkey
from ckanext.geoserver_webservice.model import GeoserverOrganizationRoleModel
from ckanext.geoserver_webservice.helpers import is_valid_uuid, get_geoserver_roles
from ckan.model import core
import ckan.plugins.toolkit as tk
import ckan.model as model
import ckan.lib.api_token as api_token

USER_VIEW_ROLES = config.get('ckanext.geoserver_webservice.user_view_roles')
DEFAULT_ROLES = config.get('ckanext.geoserver_webservice.default_roles').split()

## API ACTIONS

def geoserver_webservice_create_user_role_api_action(context, data_dict=None):
    """
    The geoserver_webservice_create_role_api_action function is used to create a new role for the user.
    The function takes in two parameters: user_id and role. The function returns a dictionary containing the 
    user name, roles and all other information about that user.

    Args:
        context: Provide the authorization context for the action
        data_dict: Pass data to the function

    Returns:
        A dictionary with the following keys:
    """
    if tk.c.userobj and tk.check_access('geoserver_user_role_modify', {'user':tk.c.userobj.name}):
        ROLE_OPTIONS = get_geoserver_roles()
        for attr in ['user_id', 'role']:
            if attr not in data_dict.keys():
                raise tk.ValidationError(f"Bad request: Invalid request. Missing {attr} parameter")
        user_id = data_dict.get('user_id')
        role = data_dict.get('role')
        user = model.User.get(user_id)
        if user is None:
            raise tk.ValidationError(f"Bad request: Invalid request. User: {id} does not exist")
        if role not in ROLE_OPTIONS:
            raise tk.ValidationError(f"Bad request: Invalid request. Role: {role} is not an allowed role, Allowed roles: {ROLE_OPTIONS}")
        try:
            GeoserverUserRoleModel(user_id=user.id, role=role).save()
            user_roles = [x.role for x in GeoserverUserRoleModel.get_user_roles(user.id) if x.state == core.State.ACTIVE]
            return {
                'user': user.name,
                'user_roles': user_roles
            }
        except Exception as e:
            raise tk.ValidationError(f"Bad request: Invalid request. {e}") 
    raise tk.NotAuthorized()

def geoserver_webservice_delete_user_role_api_action(context, data_dict=None):
    """
    The geoserver_webservice_delete_role_api_action function is used to delete a role from a user.
    It takes in the following parameters:
        context - The context of the request, which contains information about the user and their access level.
        data_dict - A dictionary that contains all of the details about what is being requested.  This function requires that you include an 'user_id' parameter with a value of whatever id you want to delete, and an 'role' parameter with a value equal to one of your roles (e.g., admin).  If everything checks out, it will return back all roles for this particular user.
    
    Args:
        context: Pass in the user object
        data_dict: Pass in the parameters that were submitted with the request
    
    Returns:
        A dictionary with the following keys:
    """
    if tk.c.userobj and tk.check_access('geoserver_user_role_modify', {'user':tk.c.userobj.name}):
        for attr in ['user_id', 'role']:
            if attr not in data_dict.keys():
                raise tk.ValidationError(f"Bad request: Invalid request. Missing {attr} parameter")
        user_id = data_dict.get('user_id')
        role = data_dict.get('role')
        user = model.User.get(user_id)
        if user is None:
            raise tk.ValidationError(f"Bad request: Invalid request. User: {id} does not exist")
        user_roles = [x for x in GeoserverUserRoleModel.get_user_roles(user.id) if x.state == core.State.ACTIVE]
        if role in [x.role for x in user_roles]:
            for geoserver_role in user_roles:
                if geoserver_role.role == role:
                    try:
                        geoserver_role.make_deleted()
                        user_roles = [x.role for x in GeoserverUserRoleModel.get_user_roles(user.id) if x.state == core.State.ACTIVE]
                        return {
                            'user': user.name,
                            'user_roles': user_roles
                        }
                    except Exception as e:
                        raise tk.ValidationError(f"Bad request: Invalid request. {e}")
        else:
            raise tk.ValidationError(f"Bad request: Invalid request. No role: {role} attached to user.")
    raise tk.NotAuthorized()

@tk.side_effect_free
def geoserver_webservice_user_roles_api_action(context, data_dict=None):
    """
    The geoserver_webservice_user_roles_api_action function is used to retrieve the roles of a user.
    It accepts a user_id parameter and returns all the roles associated with that user.
    
    Args:
        context: Provide contextual information to the function
        data_dict: Pass parameters to the function
    
    Returns:
        The roles of a user
    """
    if 'user_id' not in data_dict.keys():
        raise tk.ValidationError(f"Bad request: Invalid request. Missing user_id parameter")
    user_id = data_dict.get('user_id')
    user = tk.get_action('user_show')(context, data_dict={'id':user_id})
    if user is not None:
        user_roles = [x.role for x in GeoserverUserRoleModel.get_user_roles(user['id']) if x.state == core.State.ACTIVE]
        user_organization_ids = [x['id'] for x in tk.get_action('organization_list_for_user')({}, data_dict={'id':user_id})]
        organization_roles = []
        for org_role in GeoserverOrganizationRoleModel.get_organizations_roles(user_organization_ids):
            if org_role.state == core.State.ACTIVE and org_role.role not in organization_roles:
                organization_roles.append(org_role.role)
        result = {
                'user': user['name'],
                'user_roles': user_roles,
                'organization_roles': organization_roles,
                'default_roles': DEFAULT_ROLES}
        return result
    else:
        raise tk.ObjectNotFound('user does not exist')

@tk.side_effect_free
def geoserver_webservice_api_action(context, data_dict=None):
    """
    The geoserver_webservice_api_action function is used to authenticate a user and return the roles that they have.
    The function takes two parameters: authkey, which is either the API token or an authentication key for a user, 
    and data_dict, which contains additional information about the request.
    
    Args:
        context: Pass information about the user and the context of the request
        data_dict: Pass in the parameters that are passed to the action function
    
    Returns:
        A dictionary with the user and roles
    """
    authkey = data_dict.get('authkey')
    if is_valid_uuid(authkey):
        user = GeoserverUserAuthkey.get_user_from_authkey(authkey)
    else:
        user = api_token.get_user_from_token(authkey)
    if user is not None:
        roles = tk.get_action('get_geoserver_user_roles')({"user":user.id}, data_dict={"user_id":user.id})
        all_roles = [*set([*roles['user_roles'], *roles['organization_roles'], *roles['default_roles']])]
        role_str = ', '.join(all_roles)
        return {
                'user': roles.get('user'),
                'roles': role_str
                }
    else:
        raise tk.ObjectNotFound()

@tk.side_effect_free
def geoserver_webservice_get_user_authkey_api_action(context, data_dict={}):
    """
    The geoserver_webservice_get_user_authkey_api_action function is used to retrieve the authkey for a user.
    It takes two parameters: context and data_dict. The context parameter is automatically passed by the ReST API when calling this function, while data_dict must be manually added to the call as an extra parameter.
    
    Args:
        context: Pass information about the user and the context of the request
        data_dict: Pass parameters to the action function
    
    Returns:
        A dictionary with the username and authkey
    """

    user_id = data_dict.get('user_id') if data_dict is not None else None
    requesting_user = tk.c.userobj
    if requesting_user:
        tk.check_access('geoserver_user_authkey_get', {'user': requesting_user.name,},data_dict=data_dict)
        if user_id:
            user = tk.get_action('user_show')({}, data_dict={'id':user_id, 'include_num_followers':True})
        else:
            user = requesting_user.as_dict()
        if user:
            geoserver_authkey_obj = GeoserverUserAuthkey.get_geoserver_user_authkey_for_user(user_id=user['id'])
            if geoserver_authkey_obj:
                return {
                    'username': user['name'],
                    'authkey': geoserver_authkey_obj.authkey
                }
        else:
            raise tk.ObjectNotFound()
    raise tk.NotAuthorized()

@tk.side_effect_free
def geoserver_webservice_generate_new_user_authkey_api_action(context, data_dict={}):
    """
    The geoserver_webservice_generate_new_user_authkey_api_action function generates a new authkey for the specified user.
    
    Args:
        context: Pass information about the user and the context of the request
        data_dict: Pass in the user_id of the user.
    
    Returns:
        A dictionary with the username and authkey
    """
    user_id = data_dict.get('user_id') if data_dict is not None else None
    requesting_user = tk.c.userobj
    if requesting_user:
        tk.check_access('geoserver_user_authkey_get', {'user': requesting_user.name,},data_dict=data_dict)
        if user_id:
            user = tk.get_action('user_show')({}, data_dict={'id':user_id, 'include_num_followers':True})
        else:
            user = requesting_user.as_dict()
        if user:
            geoserver_authkey_obj = GeoserverUserAuthkey.generate_new_user_authkey(user_id=user['id'])
            if geoserver_authkey_obj:
                return {
                    'username': user['name'],
                    'authkey': geoserver_authkey_obj.authkey
                }
        else:
            raise tk.ObjectNotFound()
    raise tk.NotAuthorized()


@tk.side_effect_free
def geoserver_webservice_organization_roles_api_action(context, data_dict=None):
    """
    The geoserver_webservice_user_roles_api_action function is used to retrieve the roles of a user.
    It accepts a user_id parameter and returns all the roles associated with that user.
    
    Args:
        context: Provide contextual information to the function
        data_dict: Pass parameters to the function
    
    Returns:
        The roles of a user
    """
    if 'organization_id' not in data_dict.keys():
        raise tk.ValidationError(f"Bad request: Invalid request. Missing organization_id parameter")
    organization_id = data_dict.get('organization_id')
    org = tk.get_action('organization_show')(context, data_dict={'id':organization_id})
    if org is not None:
        organization_roles = [x.role for x in GeoserverOrganizationRoleModel.get_organization_roles(org['id']) if x.state == core.State.ACTIVE]
        result = {
                'organization': org['name'],
                'organization_roles': organization_roles}
        return result
    else:
        raise tk.ObjectNotFound('org does not exist')
    
def geoserver_webservice_create_organization_role_api_action(context, data_dict=None):
    """
    The geoserver_webservice_create_organization_role_api_action function creates a new organization role.
        
    Args:
        context: Provide contextual information to the function
        data_dict: Pass the parameters to the function
    
    Returns:
        A dictionary with the keys 'organization_id' and 'role'
    """
    if tk.c.userobj and tk.check_access('geoserver_organization_role_modify', {'user':tk.c.userobj.name}):
        ROLE_OPTIONS = get_geoserver_roles()
        for attr in ['organization_id', 'role']:
            if attr not in data_dict.keys():
                raise tk.ValidationError(f"Bad request: Invalid request. Missing {attr} parameter")
        organization_id = data_dict.get('organization_id')
        role = data_dict.get('role')
        org = tk.get_action('organization_show')(context, data_dict={'id':organization_id})
        if org is None:
            raise tk.ValidationError(f"Bad request: Invalid request. Organization: {id} does not exist")
        if role not in ROLE_OPTIONS:
            raise tk.ValidationError(f"Bad request: Invalid request. Role: {role} is not an allowed role, Allowed roles: {ROLE_OPTIONS}")
        try:
            GeoserverOrganizationRoleModel(organization_id=organization_id, role=role).save()
            organization_roles = [x.role for x in GeoserverOrganizationRoleModel.get_organization_roles(org['id']) if x.state == core.State.ACTIVE]
            return {
                'user': org['name'],
                'organization_roles': organization_roles
            }
        except Exception as e:
            raise tk.ValidationError(f"Bad request: Invalid request. {e}") 
    raise tk.NotAuthorized()

def geoserver_webservice_delete_organization_role_api_action(context, data_dict=None):
    """
    The geoserver_webservice_delete_organization_role_api_action function deletes a role from an organization.
        
    Args:
        context:  Provide contextual information to the function
        data_dict: Pass the parameters to the function
    
    Returns:
        A dictionary with the keys 'organization_id' and 'role'
    """
    if tk.c.userobj and tk.check_access('geoserver_organization_role_modify', {'user':tk.c.userobj.name}):
        for attr in ['organization_id', 'role']:
            if attr not in data_dict.keys():
                raise tk.ValidationError(f"Bad request: Invalid request. Missing {attr} parameter")
        organization_id = data_dict.get('organization_id')
        role = data_dict.get('role')
        org = tk.get_action('organization_show')(context, data_dict={'id':organization_id})
        if org is None:
            raise tk.ValidationError(f"Bad request: Invalid request. organization: {organization_id} does not exist")
        organization_roles = [x for x in GeoserverOrganizationRoleModel.get_organization_roles(org['id']) if x.state == core.State.ACTIVE]
        if role in [x.role for x in organization_roles]:
            for geoserver_role in organization_roles:
                if geoserver_role.role == role:
                    try:
                        geoserver_role.make_deleted()
                        organization_roles = [x.role for x in GeoserverOrganizationRoleModel.get_organization_roles(org['id']) if x.state == core.State.ACTIVE]
                        return {
                            'organization': org['name'],
                            'roles': organization_roles
                        }
                    except Exception as e:
                        raise tk.ValidationError(f"Bad request: Invalid request. {e}")
        else:
            raise tk.ValidationError(f"Bad request: Invalid request. No role: {role} attached to organization.")
    raise tk.NotAuthorized()

@tk.chained_action
def user_delete(up_func, context, data_dict):
    """
    The user_delete function is a custom function that allows the user to delete their own account.
    It also deletes the geoserver_user_authkey object associated with that user, if it exists.
    
    Args:
        up_func: Call the original function that was decorated
        context: Pass the user_id of the current logged in user
        data_dict: Pass parameters to the function
    
    Returns:
        orginal user_delete function 
    """
    user_id = data_dict.get("id")
    if user_id:
        geoserver_user_authkey = GeoserverUserAuthkey.get_geoserver_user_authkey_for_user(user_id)
        if geoserver_user_authkey:
            geoserver_user_authkey.make_deleted()
    return up_func(context, data_dict)

api_actions = {
    'geoserver_webservice': geoserver_webservice_api_action,
    'get_geoserver_user_roles': geoserver_webservice_user_roles_api_action,
    'create_geoserver_user_role': geoserver_webservice_create_user_role_api_action,
    'delete_geoserver_user_role': geoserver_webservice_delete_user_role_api_action,
    'get_geoserver_organization_roles': geoserver_webservice_organization_roles_api_action,
    'create_geoserver_organization_role': geoserver_webservice_create_organization_role_api_action,
    'delete_geoserver_organization_role': geoserver_webservice_delete_organization_role_api_action,
    'get_geoserver_user_authkey': geoserver_webservice_get_user_authkey_api_action,
    'generate_new_user_authkey': geoserver_webservice_generate_new_user_authkey_api_action,
    'user_delete': user_delete
}

## TEMPLATE HELPER FUNCTIONS

def get_geoserver_user_authkey_template_helper(user_id):
    """
    The get_geoserver_user_authkey_template_helper function is a helper function that returns the geoserver_user_authkey for a given user.
        
    Args:
        user_id: Get the user_id of the logged in user
    
    Returns:
        user_authkey:
    """
    if user_id is not None:
        return tk.get_action('get_geoserver_user_authkey')({}, data_dict={'user_id':user_id})

template_helper_functions = {'get_geoserver_user_authkey':get_geoserver_user_authkey_template_helper}

## AUTH FUNCTIONS

def geoserver_organization_role_view(context, data_dict=None):
    """
    The geoserver_organization_role_view function is used to determine if a user has the ability to view
    the roles of other users in an organization.

    Args:
        context: Get the auth_user_obj from the context
        data_dict: Pass in the organization_id
    
    Returns:
        A dictionary with a success key and value
    """
    auth_obj = context.get('auth_user_obj')
    if auth_obj and auth_obj.sysadmin:
        return {'success': True}
    if data_dict and auth_obj:
        if USER_VIEW_ROLES.lower() == 'true':
            org = tk.get_action('organization_show')({}, data_dict={
                'id': data_dict.get('organization_id'),
                'include_users': True})
            if org and auth_obj.id in [x['id'] for x in org['users'] if x['capacity'] == 'admin']:
                return {'success': True}
    return {'success': False}

def geoserver_organization_role_modify(context, data_dict=None):
    """
    The geoserver_organization_role_modify function is a CKAN authorization function that allows the sysadmin to modify roles for users in an organization.
        This function is used by the geoserver_organization_role_modify action plugin.
    
    Args:
        context: Get the user object from the context
        data_dict: Pass in the data from the request
    
    Returns:
        A dictionary with a key of 'success' and a value of true or false
    """
    if context.get('auth_user_obj') is not None and context['auth_user_obj'].sysadmin:
        return {'success': True}
    else:
        return {'success': False}

def geoserver_user_role_view(context, data_dict=None):
    """
    The geoserver_role_view function is used to determine whether a loged in user can view 
    geoserver roles

    Args:
        context: Pass information about the user to the function
        data_dict: Pass parameters from the api call to the function
    
    Returns:
        A dictionary with the key 'success' set to true if the user is authorized to view geoserver roles
    """
    auth_obj = context.get('auth_user_obj')
    if data_dict and auth_obj:
        if USER_VIEW_ROLES.lower() == 'true':
            if data_dict.get('user_id') in [auth_obj.id, auth_obj.name]:
                return {'success': True}
        else:
            if context.get('auth_user_obj') is not None and context['auth_user_obj'].sysadmin:
                return {'success': True}
    return {'success': False}

def geoserver_user_role_modify(context, data_dict=None):
    """ 
        The geoserver_role_modify function is used to determine whether the user has 
        permission to edit a role. It does this by checking if the user is an admin.
    Args:
        context: Provide authorization
        data_dict: Pass parameters to the function
    
    Returns:
        A dictionary with a key of success and either true or false as the value
    """
    if context.get('auth_user_obj') is not None and context['auth_user_obj'].sysadmin:
        return {'success': True}
    else:
        return {'success': False}

def geoserver_user_authkey_get(context, data_dict={}):
    """
       The geoserver_user_authkey_get function is used to determine whether the user has 
       permission to access a geoserver authkey for a user. It does this by checking if the user is 
       an admin, or if they are accessing their own geoserver instance.
    
    Args:
        context: Provide authorization functions with access to the user object
        data_dict: Pass in the user_id of the user who is trying to access the data
    
    Returns:
        A dictionary with a key of success and either true or false as the value
    """
    auth_obj = context.get('auth_user_obj')
    if auth_obj is not None:
        if auth_obj.sysadmin:
            return {'success': True}
        elif data_dict is None or data_dict.get('user_id') is None:
            return {'success': True}
        elif data_dict.get('user_id') in [auth_obj.id, auth_obj.name]:
            return {'success': True}
    return {'success': False}

auth_functions = {
    'geoserver_user_role_view': geoserver_user_role_view,
    'geoserver_user_role_modify': geoserver_user_role_modify,
    'geoserver_user_authkey_get':geoserver_user_authkey_get, 
    'geoserver_organization_role_view': geoserver_organization_role_view,
    'geoserver_organization_role_modify': geoserver_organization_role_modify
}