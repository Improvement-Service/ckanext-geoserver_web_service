import uuid 
import requests
import logging
from requests.auth import HTTPBasicAuth
from ckan.common import config

GEOSERVER_URL = config.get('ckanext.geoserver_webservice.url')
GEOSERVER_USERNAME = config.get('ckanext.geoserver_webservice.username')
GEOSERVER_PASSWORD = config.get('ckanext.geoserver_webservice.password')
DEFAULT_ROLES = config.get('ckanext.geoserver_webservice.default_roles').split()
log = logging.getLogger(__name__)

def get_geoserver_roles():
    try:
        basic = HTTPBasicAuth(GEOSERVER_USERNAME, GEOSERVER_PASSWORD)
        roles_url = f"{GEOSERVER_URL}/rest/security/roles.json"
        response = requests.get(roles_url, auth=basic)
        if response.status_code != 200:
            log.error('Failed to fetch local geoserver role options')
            return []
        else:
            all_roles = response.json().get('roles', [])
            options_roles = [x[5:] for x in all_roles if x.startswith('ROLE_')]
            options_roles = [x for x in options_roles if x not in DEFAULT_ROLES]
            return options_roles
    except Exception as e:
        log.error(e)
        log.error('Failed to fetch local geoserver role options')
    return []
    
def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False