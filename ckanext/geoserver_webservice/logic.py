from ckan.common import config

USER_VIEW_ROLES = config.get('ckanext.geoserver_webservice.user_view_roles')

def geoserver_role_view(context, data_dict=None):
    auth_obj = context.get('auth_user_obj')
    if data_dict and auth_obj:
        if USER_VIEW_ROLES.lower() == 'true':
            if data_dict.get('user_id') in [auth_obj.id, auth_obj.name]:
                return {'success': True}
        else:
            if context.get('auth_user_obj') is not None and context['auth_user_obj'].sysadmin:
                return {'success': True}

    return {'success': False}
        

def geoserver_role_modify(context, data_dict=None):
    if context.get('auth_user_obj') is not None and context['auth_user_obj'].sysadmin:
        return {'success': True}
    else:
        return {'success': False}

def geoserver_user_authkey_get(context, data_dict={}):
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
    'geoserver_role_view': geoserver_role_view,
    'geoserver_role_modify': geoserver_role_modify,
    'geoserver_user_authkey_get':geoserver_user_authkey_get
}