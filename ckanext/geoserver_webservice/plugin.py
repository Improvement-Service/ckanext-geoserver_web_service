import ckan.plugins as pl
import ckan.plugins.toolkit as tk
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
from ckanext.geoserver_webservice.model import GeoserverUserRoleModel
from ckanext.geoserver_webservice.model import GeoserverOrganizationRoleModel
from ckanext.geoserver_webservice.logic import auth_functions, api_actions, template_helper_functions
from ckanext.geoserver_webservice.helpers import get_geoserver_roles

log = logging.getLogger(__name__)

DEFAULT_ROLES = config.get('ckanext.geoserver_webservice.default_roles').split()

class GeoserverWebservicePlugin(pl.SingletonPlugin):
    pl.implements(pl.IConfigurer)
    pl.implements(pl.IBlueprint)
    pl.implements(pl.IActions)
    pl.implements(pl.IAuthFunctions)
    pl.implements(pl.ITemplateHelpers)

    @staticmethod
    def get_auth_functions():
        return auth_functions

    @staticmethod
    def get_helpers():
        return template_helper_functions
    
    @staticmethod
    def get_actions():
        return api_actions

    #IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic', 'geoserver_webservice')
        # Add geoserver roles table if does not already exist
        init_tables()

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
            'read_user_roles',
            controller.geoserver_user_roles_read,
            methods=['GET'])

        blueprint.add_url_rule(
            '/user/<user_id>/geoserver-roles/delete/<role_id>',
            'delete_user_role',
            controller.geoserver_user_roles_delete,
            methods=['POST'])

        blueprint.add_url_rule(
            '/user/<user_id>/geoserver-roles/add',
            'add_user_role',
            controller.geoserver_user_roles_add,
            methods=['POST'])
        
        blueprint.add_url_rule(
            '/user/<user_id>/geoserver-roles/refresh_authkey',
            'refresh_user_authkey',
            controller.geoserver_refresh_user_authkey,
            methods=['GET'])
        
        blueprint.add_url_rule(
            '/organization/geoserver-roles/<organization_id>',
            'read_organization_roles',
            controller.geoserver_organization_roles_read,
            methods=['GET'])
        
        blueprint.add_url_rule(
            '/organization/geoserver-roles/<organization_id>/add',
            'add_organization_role',
            controller.geoserver_organization_roles_add,
            methods=['POST']
        )

        blueprint.add_url_rule(
            '/organization/geoserver-roles/<organization_id>/delete/<role_id>',
            'delete_organization_role',
            controller.geoserver_organization_roles_delete,
            methods=['POST'])

        return blueprint

class GeoserverWebServiceController():

    def geoserver_user_roles_read(self, user_id, errors=None):
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
        
        if tk.c.userobj and tk.check_access('geoserver_user_role_view', {'user':tk.c.userobj.name}, data_dict={'user_id':user_id}):
            ROLE_OPTIONS = get_geoserver_roles()
            user = tk.get_action('user_show')({}, data_dict={'id':user_id, 'include_num_followers':True})
            user_roles = [x for x in GeoserverUserRoleModel.get_user_roles(user.get('id')) if x.state == core.State.ACTIVE]
            user_organizations = tk.get_action('organization_list_for_user')({}, data_dict={'id':user_id})
            organization_roles = []
            for org in user_organizations:
                result = tk.get_action('get_geoserver_organization_roles')({}, data_dict={'organization_id': org['id']})
                organization_roles = [*organization_roles, *result['organization_roles']]
            role_options = [{'value':x,'text':x} for x in ROLE_OPTIONS if x not in [x.role for x in user_roles]]
            role_options = [{'value':'null', 'text':'Select Role'}, *role_options]
            return render_template('user/geoserver_role_read.html',
                user_dict=user,
                user_roles=user_roles,
                organization_roles=organization_roles ,
                default_roles=DEFAULT_ROLES,
                role_options=role_options,
                errors=errors)
        raise NotAuthorized
    
    def geoserver_user_roles_delete(self, user_id, role_id):
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
            if tk.c.userobj and tk.check_access('geoserver_user_role_modify', {'user':tk.c.userobj.name}):
                try:
                    GeoserverUserRoleModel.get(role_id=role_id).make_deleted()
                    log.info(f'removing role_id: {role_id} from user: {user_id}')
                except Exception as e:
                    log.error(e)
                    errors = {'error':'Failed To Delete Role', 'context':'Failed to delete role from user.'}
                    return self.geoserver_user_roles_read(user_id, errors)
        return redirect(f"/user/{user_id}/geoserver-roles", code=302)
    
    def geoserver_user_roles_add(self, user_id):
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
            ROLE_OPTIONS = get_geoserver_roles()
            if tk.c.userobj and tk.check_access('geoserver_user_role_modify', {'user':tk.c.userobj.name}):
                user = tk.get_action('user_show')({}, data_dict={'id':user_id, 'include_num_followers':True})
                role = request.form.get('role_name')
                if role in ROLE_OPTIONS:
                    try:
                        GeoserverUserRoleModel(user_id=user.get('id'), role=role).save()
                        log.info(f'added role: {role} to user: {user_id}')
                    except Exception as e:
                        log.error(e)
                        errors = {'error':'Failed To Add Role', 'context':'Unexpected error occurred when adding role to user'}
                        return self.geoserver_user_roles_read(user_id, errors)
                else:
                    errors = {'error':'Failed To Add Role', 'context':'Invalid role entry'}
                    return self.geoserver_user_roles_read(user_id, errors)
        return redirect(f"/user/{user_id}/geoserver-roles", code=302)

    
    def geoserver_organization_roles_read(self, organization_id, errors=None):
        """
        The geoserver_organization_roles_read function is used to display the roles of a given organization.
            
        Args:
            self: Pass the object to the function
            organization_id: Get the organization from the database
            errors: Display errors in the template
        
        Returns:
            The geoserver_organization_roles_read template
        
        """
        if tk.c.userobj and tk.check_access('geoserver_organization_role_view', {'user':tk.c.userobj.name}, data_dict={'organization_id':organization_id}):
            ROLE_OPTIONS = get_geoserver_roles()
            org = tk.get_action('organization_show')({}, data_dict={'id':organization_id,'include_users': True})
            org_roles = [x for x in GeoserverOrganizationRoleModel.get_organization_roles(org.get('id')) if x.state == core.State.ACTIVE]
            role_options = [{'value':x,'text':x} for x in ROLE_OPTIONS if x not in [x.role for x in org_roles]]
            role_options = [{'value':'null', 'text':'Select Role'}, *role_options]
            return render_template('organization/geoserver_role_read.html',
                                group_dict=org,
                                group_type='organization',
                                organization_roles=org_roles,
                                role_options=role_options,
                                errors=errors
                                )
        raise NotAuthorized
        
    def geoserver_organization_roles_add(self, organization_id):
        """
        The geoserver_organization_roles_add function adds a role to an organization.
            
        Args:
            self: Refer to the class itself
            organization_id: ID of the organization.
        
        Returns:
            A redirect to the geoserver_organization_roles_read function
        """
        if request.environ['REQUEST_METHOD'] == 'POST':
            ROLE_OPTIONS = get_geoserver_roles()
            if tk.c.userobj and tk.check_access('geoserver_organization_role_modify', {'user':tk.c.userobj.name}):
                org = tk.get_action('organization_show')({}, data_dict={'id':organization_id,'include_users': True})
                role = request.form.get('role_name')
                if role in ROLE_OPTIONS:
                    try:
                        GeoserverOrganizationRoleModel(organization_id=org.get('id'), role=role).save()
                        log.info(f'added role: {role} to organization: {organization_id}')
                    except Exception as e:
                        errors = {'error':'Failed To Add Role', 'context':'Unexpected error occurred when adding role to organization'}
                        return self.geoserver_organization_roles_read(organization_id, errors)
                else:
                    errors = {'error':'Failed To Add Role', 'context':'Invalid role entry'}
                    return self.geoserver_organization_roles_read(organization_id, errors)
            else:
                raise NotAuthorized
        return redirect(f"/organization/geoserver-roles/{organization_id}", code=302)
    
    def geoserver_organization_roles_delete(self, organization_id, role_id):
        """
        The geoserver_organization_roles_delete function is used to delete a role from an organization.
        
        Args:
            self: Refer to the class itself and is used for accessing variables that belongs to the class
            organization_id: ID of the organization.
            role_id: ID the role to be deleted
        
        Returns:
            A redirect to the geoserver_organization_roles_read function
        """
        if request.environ['REQUEST_METHOD'] == 'POST':
            if tk.c.userobj and tk.check_access('geoserver_organization_role_modify', {'user':tk.c.userobj.name}):
                org = tk.get_action('organization_show')({}, data_dict={'id':organization_id})
                if org:
                    try:
                        GeoserverOrganizationRoleModel.get(role_id=role_id).make_deleted()
                        log.info(f'removing role_id: {role_id} from organization: {org["name"]}')
                    except Exception as e:
                        log.error(e)
                        errors = {'error':'Failed To Delete Role', 'context':'Failed to delete role from user.'}
                        return self.geoserver_organization_roles_read(org['id'], errors)
            else:
                raise NotAuthorized
        return redirect(f"/organization/geoserver-roles/{organization_id}", code=302)
    
    def geoserver_refresh_user_authkey(self, user_id):
        """
        The geoserver_refresh_user_authkey function is used to refresh the authkey of a user.
        
        Args:
            self: Refer to the class itself
            user_id: Id the user
        
        Returns:
            A redirect to the geoserver_user_roles_read function
        """
        if tk.c.userobj and tk.check_access('geoserver_user_authkey_get', {'user':tk.c.userobj.name}):
            try:
                tk.get_action('generate_new_user_authkey')({}, data_dict={'user_id':user_id})
            except Exception as e:
                log.error(e)
                errors = {'error':'Failed to refresh authkey', 'context':'Failed to refresh geoserver user authkey'}
                return self.geoserver_user_roles_read(user_id, errors)
        else:
            raise NotAuthorized
        return redirect(f"/user/{user_id}/geoserver-roles", code=302)
