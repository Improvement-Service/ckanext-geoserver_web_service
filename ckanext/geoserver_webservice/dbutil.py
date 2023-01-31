from sqlalchemy import Table, Column, Integer, Text, MetaData, update, DateTime, ForeignKey, types
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
from sqlalchemy import exc as sa_exc
# from ckanext.geoserver_webservice.models import GeoserverRole
from ckanext.geoserver_webservice.model import GeoserverRoleModel

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
        geoserver_roles = Table(
                            'geoserver_role', metadata,
                            Column('id', types.UnicodeText, primary_key=True, nullable=False, index=True, default=_types.make_uuid),
                            Column('user_id', types.UnicodeText, ForeignKey("user.id"), index=True),
                            Column('role', Text,  nullable=False),
                            Column('state', types.UnicodeText, default=core.State.ACTIVE),
                            Column('created', DateTime, default=datetime.datetime.now),
                            Column('last_modified', DateTime, default=datetime.datetime.now),
                            Column('closed', DateTime),
                            )
        metadata.create_all(engine)
    # print(GeoserverRoleModel.get_user_roles("dd499db2-495e-438e-8b13-2f3a6e28c635"))
    # role = GeoserverRoleModel.get("ac39de80-f798-41aa-892c-07ea5a81ef2d")
    # print(role)
    # role.make_deleted()
    # role = GeoserverRoleModel.get('1')
    # print(role)
    # print(GeoserverRoleModel.add)
    # x = GeoserverRoleModel(user_id="dd499db2-495e-438e-8b13-2f3a6e28c635", role='PSGA')
    # print(x)
    # x.save()

    # sql = model.Session.query(GeoserverRoleModel).filter_by(id='1')
    # result = model.Session.execute(sql).fetchall()
    # print(result)


    # connection = model.Session.Query
    # table = get_table(name='user')
    # print(type(table))
    # user_name = "tom_jones"
    # filter = text(f"""
    #         "user".name = '{user_name}'
    #     """)
    # item = model.Session.query(model.User).filter_by(name='tom_jones')
    # print(item)
    # print(model.Session.execute(item).fetchone())

    # stmt = select(User).where(User.name == "tom_jones")
    # model.Session.Excecute(stmt)
    # included_parts = model.Session.query(
    #             User.name,).\
    #                 filter(User.name=="tom_jones").\
    #                 cte(name="included_parts", recursive=True)

# def get_user_roles(user_id: str):
#     """
#     The get_user_roles function accepts a user_id and returns all the roles associated with that user.
    
#     Args:
#         user_id: str: Pass the user_id to the sql query
    
#     Returns:
#         A list of geoserver role objects
    
#     """
#     connection = model.Session.connection()

#     try:
#         user_roles = connection.execute(
#             text("""
#             SELECT * FROM public.geoserver_role 
#             WHERE user_id = :user_id"""), user_id=user_id).fetchall()
#         return list(map(lambda role: GeoserverRole(**role), user_roles))
#     except Exception as e:
#         log.error(e)
#         raise Exception from(e)

# def purge_all_deleted_roles():
#     connection = model.Session.connection()
#     try:
#         connection.execute(
#             text("""
#                 DELETE FROM public.geoserver_role
#                 WHERE state = :state
#             """), state='Deleted')
#         model.Session.commit()
#     except Exception as e:
#         log.error(e)
#         raise Exception from(e)

def get_user_from_apikey(apikey):
    try:
        sql = model.Session.query(model.User).filter_by(apikey=apikey)
        result = model.Session.execute(sql).fetchall()
        if len(result) > 0:
            return User.get(result[0].user_id)
    except Exception as e:
        log.error(e)
        raise Exception from(e)

def ignore_sqlwarnings(sqlachemy_func):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        return sqlachemy_func()