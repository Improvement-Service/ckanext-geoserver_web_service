from sqlalchemy import Table, Column, Integer, String, Text, MetaData, update
from sqlalchemy.sql import select, text
from sqlalchemy import func

import ckan.model as model
from ckan.lib.base import *
from ckanext.geoserver_webservice.models import GeoserverRole

import logging

log = logging.getLogger(__name__)

def init_tables():
    engine = model.meta.engine
    if not engine.dialect.has_table(engine, 'geoserver_role'):
        metadata = MetaData()
        geoserver_roles = Table('geoserver_role', metadata,
                            Column('id', Integer, primary_key=True),
                            Column('user_id', Text),
                            Column('role', Text),
                            Column('state', Text))
        metadata.create_all(engine)

def get_user_roles(user_id: str):
    connection = model.Session.connection()
    try:
        user_roles = connection.execute(
            text("""
            SELECT * FROM public.geoserver_role 
            WHERE user_id = :user_id"""), user_id=user_id).fetchall()
        return list(map(lambda role: GeoserverRole(*role), user_roles))
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
