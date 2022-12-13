import ckan.plugins as pl
import ckan.plugins.toolkit as tk
import ckan.lib.api_token as api_token
import logging
from ckan.common import config, request
from ckan.logic import NotAuthorized
from flask import Blueprint
from flask import redirect
from flask import render_template, render_template_string
from ckan.authz import is_authorized
from ckanext.geoserver_webservice.dbutil import init_tables, get_user_roles
from ckanext.geoserver_webservice.models import GeoserverRole

log = logging.getLogger(__name__)

DEFAULT_ROLES = config.get('ckanext.geoserver_webservice.default_roles').split()
ROLE_OPTIONS = config.get('ckanext.geoserver_webservice.role_options').split()

@tk.side_effect_free
def geoserver_webservice(context, data_dict=None):
    user = api_token.get_user_from_token(data_dict.get('authkey'))
    if user is not None:
        user_roles = [x.role for x in get_user_roles(user.id) if x.state == 'Active']
        all_roles = [*DEFAULT_ROLES, *user_roles]
        role_str = ', '.join(all_roles)
        result = {
                'username': user.name,
                'roles': role_str}
        return result
    else:
        raise tk.ObjectNotFound()

class GeoserverWebservicePlugin(pl.SingletonPlugin):
    pl.implements(pl.IConfigurer)
    pl.implements(pl.IBlueprint)
    pl.implements(pl.IActions)

    # IConfigurer
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
            'geoserver_webservice':geoserver_webservice
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
        if tk.c.userobj is not None and tk.c.userobj.sysadmin == True:
            user = tk.get_action('user_show')({}, data_dict={'id':user_id, 'include_num_followers':True})
            user_roles = [x for x in get_user_roles(user.get('id')) if x.state == 'Active']
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
            if tk.c.userobj is not None and tk.c.userobj.sysadmin == True:
                try:
                    GeoserverRole(id=role_id).delete()
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
            if tk.c.userobj is not None and tk.c.userobj.sysadmin == True:
                user = tk.get_action('user_show')({}, data_dict={'id':user_id, 'include_num_followers':True})
                role = request.form.get('role_name')
                if role in ROLE_OPTIONS:
                    try:
                        GeoserverRole(user_id=user.get('id'), role=role).save()
                        log.info(f'added role: {role} to user: {user_id}')
                    except Exception as e:
                        log.error(e)
                        errors = {'error':'Failed To Add Role', 'context':'Unexpected error occurred when adding role to user'}
                        return self.geoserver_roles_read(user_id, errors)
                else:
                    errors = {'error':'Failed To Add Role', 'context':'Invalid role entry'}
                    return self.geoserver_roles_read(user_id, errors)
        return redirect(f"/user/{user_id}/geoserver-roles", code=302)


