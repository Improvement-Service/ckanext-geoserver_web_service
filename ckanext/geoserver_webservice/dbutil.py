from sqlalchemy import Table, Column, Integer, Text, MetaData, update, DateTime
from sqlalchemy.sql import text, func
from sqlalchemy import func
import ckan.model as model
import datetime
from ckan.lib.base import *
import warnings
from sqlalchemy import exc as sa_exc
from ckanext.geoserver_webservice.models import GeoserverRole

import logging

log = logging.getLogger(__name__)

def init_tables():
    engine = model.meta.engine
    metadata = MetaData()
    if not engine.dialect.has_table(engine, 'geoserver_role'):
        geoserver_roles = Table(
                            'geoserver_role',
                            metadata,
                            Column('id', Integer, primary_key=True, nullable=False, index=True),
                            Column('user_id', Text, nullable=False, index=True),
                            Column('role', Text,  nullable=False),
                            Column('state', Text, nullable=False),
                            Column('created', DateTime, server_default=func.now()),
                            Column('last_modified', DateTime, server_default=func.now()),
                            Column('closed', DateTime),
                            )
        metadata.create_all(engine)

def get_user_roles(user_id: str):
    print(datetime.datetime.now)
    connection = model.Session.connection()
    try:
        user_roles = connection.execute(
            text("""
            SELECT * FROM public.geoserver_role 
            WHERE user_id = :user_id"""), user_id=user_id).fetchall()
        return list(map(lambda role: GeoserverRole(**role), user_roles))
    except Exception as e:
        log.error(e)
        raise Exception from(e)

def purge_all_deleted_roles():
    connection = model.Session.connection()
    try:
        connection.execute(
            text("""
                DELETE FROM public.geoserver_role
                WHERE state = :state
            """), state='Deleted')
        model.Session.commit()
    except Exception as e:
        log.error(e)
        raise Exception from(e)


def ignore_sqlwarnings(sqlachemy_func):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        return sqlachemy_func()