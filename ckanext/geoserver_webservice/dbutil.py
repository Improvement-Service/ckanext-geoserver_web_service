from ckanext.geoserver_webservice.model import GeoserverOrganizationRoleModel
from ckanext.geoserver_webservice.model import GeoserverUserRoleModel
from ckanext.geoserver_webservice.model import GeoserverUserAuthkey

import logging

log = logging.getLogger(__name__)

def init_tables():
    """
    The init_tables function creates the geoserver_role table in the database if it does not already exist.
    
    Returns:
        None
    """
    if not GeoserverOrganizationRoleModel.__table__.exists():
        GeoserverOrganizationRoleModel.__table__.create()
    if not GeoserverUserRoleModel.__table__.exists():
        GeoserverUserRoleModel.__table__.create()
    if not GeoserverUserAuthkey.__table__.exists():
        GeoserverUserAuthkey.__table__.create()

def drop_tables():
    """
    The drop_tables function drops the tables in the database.

    Returns:
        None
    """
    if not GeoserverOrganizationRoleModel.__table__.exists():
        GeoserverOrganizationRoleModel.__table__.drop()
    if not GeoserverUserRoleModel.__table__.exists():
        GeoserverUserRoleModel.__table__.drop()
    if not GeoserverUserAuthkey.__table__.exists():
        GeoserverUserAuthkey.__table__.drop()
