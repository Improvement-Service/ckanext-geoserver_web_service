import uuid 
import requests

import logging
from requests.auth import HTTPBasicAuth
from requests_cache import CachedSession, RedisCache
from ckan.common import config

REDIS_CONNECTION = config.get('ckan.redis.url', 'redis://localhost:6379/0')

log = logging.getLogger(__name__)
redis_host, redis_port = REDIS_CONNECTION.split('/')[2].split(':')
backend = RedisCache(host=redis_host, port=redis_port)
session = CachedSession('http_cache', backend=backend)
session.settings.expire_after = 300
session.settings.stale_if_error = True

def get_geoserver_roles():
    try:
        geoserver_url = config.get('ckanext.geoserver_webservice.url')
        geoserver_username = config.get('ckanext.geoserver_webservice.username')
        geoserver_password = config.get('ckanext.geoserver_webservice.password')
        default_roles = config.get('ckanext.geoserver_webservice.default_roles', '').split()

        log.info("GEOSERVER_USERNAME: %s", geoserver_username)
        log.info("GEOSERVER_URL: %s", geoserver_url)

        if not geoserver_url or not geoserver_username or not geoserver_password:
            log.error("Missing GeoServer config values")
            return []

        basic = HTTPBasicAuth(geoserver_username, geoserver_password)
        roles_url = f"{geoserver_url}/rest/security/roles.json"
        response = session.get(roles_url, auth=basic)

        if response.status_code != 200:
            log.error("Failed to fetch local geoserver role options")
            return []

        all_roles = response.json().get('roles', [])
        options_roles = [x[5:] for x in all_roles if x.startswith('ROLE_')]
        options_roles = [x for x in options_roles if x not in default_roles]
        return options_roles

    except Exception as e:
        log.exception("Failed to fetch local geoserver role options: %s", e)
        return []
    
def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False