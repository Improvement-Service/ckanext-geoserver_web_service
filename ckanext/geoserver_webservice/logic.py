from ckan.common import config

USER_VIEW_ROLES = config.get('ckanext.geoserver_webservice.user_view_roles')

def geoserver_role_view(context, data_dict=None):
    if USER_VIEW_ROLES.lower() == 'true':
        if context.get('auth_user_obj') is not None:
            return {'success': True}
    else:
        if context.get('auth_user_obj') is not None and context['auth_user_obj'].sysadmin:
            return {'success': True}
        else:
            return {'success': False}
        

def geoserver_role_modify(context, data_dict=None):
    if context.get('auth_user_obj') is not None and context['auth_user_obj'].sysadmin:
        return {'success': True}
    else:
        return {'success': False}


auth_functions = {
    'geoserver_role_view': geoserver_role_view,
    'geoserver_role_modify': geoserver_role_modify
}