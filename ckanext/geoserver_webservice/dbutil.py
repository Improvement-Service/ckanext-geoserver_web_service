from ckan.model import meta
from ckanext.geoserver_webservice.model import (
    GeoserverOrganizationRoleModel,
    GeoserverUserRoleModel,
    GeoserverUserAuthkey,
)
import logging

log = logging.getLogger(__name__)


def init_tables():
    """
    Create GeoServer-related tables if they do not already exist.
    Safe to call multiple times.
    """
    engine = meta.engine

    log.info("Ensuring GeoServer tables exist")

    GeoserverOrganizationRoleModel.__table__.create(
        bind=engine, checkfirst=True
    )
    GeoserverUserRoleModel.__table__.create(
        bind=engine, checkfirst=True
    )
    GeoserverUserAuthkey.__table__.create(
        bind=engine, checkfirst=True
    )


def drop_tables():
    """
    Drop GeoServer-related tables if they exist.
    """
    engine = meta.engine

    log.info("Dropping GeoServer tables (if they exist)")

    GeoserverOrganizationRoleModel.__table__.drop(
        bind=engine, checkfirst=True
    )
    GeoserverUserRoleModel.__table__.drop(
        bind=engine, checkfirst=True
    )
    GeoserverUserAuthkey.__table__.drop(
        bind=engine, checkfirst=True
    )
