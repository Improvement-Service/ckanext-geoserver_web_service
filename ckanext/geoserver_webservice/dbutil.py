from sqlalchemy import Table, Column, Integer, Text, MetaData, update, DateTime, ForeignKey, types, orm
from sqlalchemy import select
from sqlalchemy.sql import text, func
from sqlalchemy import func
import ckan.model as model
from ckan.model.user import User
from ckan.model import meta, core, domain_object
from ckan.model import types as _types
import datetime
from ckan.lib.base import *
import warnings
from ckan.model.meta import metadata, mapper, Session
from sqlalchemy import exc as sa_exc
# from ckanext.geoserver_webservice.models import GeoserverRole
from ckanext.geoserver_webservice.model import GeoserverRoleModel
from ckanext.geoserver_webservice.model import GeoserverUserAuthkey

import logging

log = logging.getLogger(__name__)


cached_tables = {}


def init_tables():
    """
    The init_tables function creates the geoserver_role table in the database if it does not already exist.
    
    Returns:
        A metadata object
    """
    engine = model.meta.engine
    metadata = MetaData()
    if not engine.dialect.has_table(engine, 'geoserver_role'):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=sa_exc.SAWarning)
            metadata.reflect(bind=engine)
        geoserver_role_table = Table(
                            'geoserver_role', metadata,
                            Column('id', types.UnicodeText, primary_key=True, nullable=False, index=True, default=_types.make_uuid),
                            Column('user_id', types.UnicodeText,  ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"), index=True),
                            Column('role', Text,  nullable=False),
                            Column('state', types.UnicodeText, default=core.State.ACTIVE),
                            Column('created', DateTime, default=datetime.datetime.now),
                            Column('last_modified', DateTime, default=datetime.datetime.now),
                            Column('closed', DateTime),
                            )
        metadata.create_all(engine)
    if not engine.dialect.has_table(engine, 'geoserver_user_authkey'):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=sa_exc.SAWarning)
            metadata.reflect(bind=engine)
        geoserver_user_authkey_table = Table(
                            'geoserver_user_authkey', metadata,
                            Column('authkey', types.UnicodeText, primary_key=True, nullable=False, index=True, default=_types.make_uuid),
                            Column('user_id', types.UnicodeText, ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"), index=True),
                            Column('state', types.UnicodeText, default=core.State.ACTIVE),
                            Column('created', DateTime, default=datetime.datetime.now, nullable=False),
                            Column('last_access', DateTime, nullable=True),
                            Column('closed', DateTime, nullable=True),
        )

        metadata.create_all(engine)


def ignore_sqlwarnings(sqlachemy_func):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        return sqlachemy_func()