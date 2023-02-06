import ckan.plugins as pl
import ckan.plugins.toolkit as tk
import ckan.lib.api_token as api_token
import logging
from ckan.common import config, request
from ckan.logic import NotAuthorized
from ckan.model import core
import ckan.model as model
from flask import Blueprint
from flask import redirect
from flask import render_template, render_template_string
from ckan.authz import is_authorized
from ckanext.geoserver_webservice.dbutil import init_tables
from ckanext.geoserver_webservice.model import GeoserverRoleModel
from ckanext.geoserver_webservice.model import GeoserverUserAuthkey
from ckanext.geoserver_webservice.logic import auth_functions
from ckanext.geoserver_webservice.helpers import is_valid_uuid
from ckan.logic.action.delete import user_delete 

log = logging.getLogger(__name__)

DEFAULT_ROLES = config.get('ckanext.geoserver_webservice.default_roles').split()
ROLE_OPTIONS = config.get('ckanext.geoserver_webservice.role_options').split()

@tk.side_effect_free
def geoserver_webservice_api_action(context, data_dict=None):
    authkey = data_dict.get('authkey') 
    if is_valid_uuid(authkey):
        user = GeoserverUserAuthkey.get_user_from_authkey(authkey)
    else:
        user = api_token.get_user_from_token(authkey)
    if user is not None:
        user_roles = [x.role for x in GeoserverRoleModel.get_user_roles(user.id) if x.state == core.State.ACTIVE]
        all_roles = [*DEFAULT_ROLES, *user_roles]
        role_str = ', '.join(all_roles)
        result = {
                'username': user.name,
                'roles': role_str}
        return result
    else:
        raise tk.ObjectNotFound()

@tk.side_effect_free
def get_geoserver_user_authkey_api_action(context, data_dict={}):
    user_id = data_dict.get('user_id') if data_dict is not None else None
    requesting_user = tk.c.userobj
    if requesting_user:
        tk.check_access('geoserver_user_authkey_get',{'user': requesting_user.name,},data_dict=data_dict)
        if user_id:
            user = tk.get_action('user_show')({}, data_dict={'id':user_id, 'include_num_followers':True})
        else:
            user = requesting_user.as_dict()
        if user:
            geoserver_authkey_obj = GeoserverUserAuthkey.get_geoserver_user_authkey_for_user(user_id=user['id'])
            return {
                'username': user['name'],
                'authkey': geoserver_authkey_obj.authkey
            }
        else:
            raise tk.ObjectNotFound()
    raise tk.NotAuthorized()

def get_geoserver_user_authkey_template_helper(user_id):
    if user_id is not None:
        return tk.get_action('get_geoserver_user_authkey')({}, data_dict={'user_id':user_id})

class GeoserverWebservicePlugin(pl.SingletonPlugin):
    pl.implements(pl.IConfigurer)
    pl.implements(pl.IBlueprint)
    pl.implements(pl.IActions)
    pl.implements(pl.IAuthFunctions)
    pl.implements(pl.ITemplateHelpers)

    @staticmethod
    def get_auth_functions():
        return auth_functions

    def get_helpers(self):
        """
        helper functions accessable from templates.
        """
        return {'get_geoserver_user_authkey':get_geoserver_user_authkey_template_helper}

    #IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic',
            'geoserver_webservice')
        # Add geoserver roles table if does not already exist/
        init_tables()

    @staticmethod
    def get_actions():
        """ Should return a dict, the keys being the name of 
            the logic function and the values being the functions themselves.
        """
        return {
                'geoserver_webservice':geoserver_webservice_api_action,
                'get_geoserver_user_authkey': get_geoserver_user_authkey_api_action,
            }

    def get_blueprint(self):
        '''
            Return a Flask Blueprint object to be registered by the app.
        '''

        controller = GeoserverWebServiceController()
        #Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)

        blueprint.template_folder = 'templates'

        blueprint.add_url_rule(
            '/user/<user_id>/geoserver-roles/',
            'read',
            controller.geoserver_roles_read,
            methods=['GET'])

        blueprint.add_url_rule(
            '/user/<user_id>/geoserver-roles/delete/<role_id>',
            'delete',
            controller.geoserver_roles_delete,
            methods=['POST'])

        blueprint.add_url_rule(
            '/user/<user_id>/geoserver-roles/add',
            'add',
            controller.geoserver_roles_add,
            methods=['POST'])

        return blueprint

class GeoserverWebServiceController():
    def geoserver_roles_read(self, user_id, errors=None):
        """
        The geoserver_roles_read function is used to render the geoserver_roles_read.html template,
        which allows users with sysadmin privileges to view all roles for a given user. This function also
        provides an interface for adding and removing roles from a user.
        
        Args:
            self: Access the class instance
            user_id: Identify the user
            errors=None: Pass errors back to the form, if there are any
        
        Returns:
            A page that allows the user to select a role for the specified user
        """
        if tk.check_access('geoserver_role_view', {'user':tk.c.userobj.name}, data_dict={'user_id':user_id}):
            user = tk.get_action('user_show')({}, data_dict={'id':user_id, 'include_num_followers':True})
            user_roles = [x for x in GeoserverRoleModel.get_user_roles(user.get('id')) if x.state == core.State.ACTIVE]
            role_options = [{'value':x,'text':x} for x in ROLE_OPTIONS if x not in [x.role for x in user_roles]]
            role_options = [{'value':'null', 'text':'Select Role'}, *role_options]
            return render_template('user/geoserver_role_read.html',
                user_dict = user,
                user_roles= user_roles,
                default_roles = DEFAULT_ROLES,
                role_options= role_options,
                errors=errors)
        raise NotAuthorized
    
    def geoserver_roles_delete(self, user_id, role_id):
        """
        The geoserver_roles_delete function is used to delete a role from a user.
        It takes two arguments, the first being the user_id and the second being the role_id.
        The function then checks if there are any errors in deleting and redirects back to 
        the geoserver-roles page for that particular user.
        
        Args:
            self: Access the class instance
            user_id: ID of user that the role is being removed from.
            role_id: ID of role that is to be removed from the user.
        
        Returns:
            A redirect to the user's geoserver_roles page
        """
        if request.environ['REQUEST_METHOD'] == 'POST':
            if tk.check_access('geoserver_role_modify', {'user':tk.c.userobj.name}):
                try:
                    GeoserverRoleModel.get(role_id=role_id).make_deleted()
                    log.info(f'removing role_id: {role_id} from user: {user_id}')
                except Exception as e:
                    log.error(e)
                    errors = {'error':'Failed To Delete Role', 'context':'Failed to delete role from user.'}
                    return self.geoserver_roles_read(user_id, errors)
        return redirect(f"/user/{user_id}/geoserver-roles", code=302)
    
    def geoserver_roles_add(self, user_id):
        """
        The geoserver_roles_add function adds a role to the user.
        It takes one argument, user_id. The function then checks if
        there are any errors in deleting and redirects back to 
        the geoserver-roles page for that particular user.
        
        Args:
            self: Access the class instance
            user_id: ID of user that the role is being added too.
        
        Returns:
            A redirect to the user's geoserver roles page

        """
        if request.environ['REQUEST_METHOD'] == 'POST':
            if tk.check_access('geoserver_role_modify', {'user':tk.c.userobj.name}):
                user = tk.get_action('user_show')({}, data_dict={'id':user_id, 'include_num_followers':True})
                role = request.form.get('role_name')
                if role in ROLE_OPTIONS:
                    try:
                        GeoserverRoleModel(user_id=user.get('id'), role=role).save()
                        log.info(f'added role: {role} to user: {user_id}')
                    except Exception as e:
                        log.error(e)
                        errors = {'error':'Failed To Add Role', 'context':'Unexpected error occurred when adding role to user'}
                        return self.geoserver_roles_read(user_id, errors)
                else:
                    errors = {'error':'Failed To Add Role', 'context':'Invalid role entry'}
                    return self.geoserver_roles_read(user_id, errors)
        return redirect(f"/user/{user_id}/geoserver-roles", code=302)
