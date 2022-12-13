from __future__ import absolute_import

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import select, text, func
from ckan.lib.dictization import table_dictize

from .base import Base


class GeoserverRoleModel():
    __tablename__ = 'geoserver_role'

    id = Column('id', Integer, primary_key=True, nullable=False, index=True)
    user_id = Column('user_id', Text, nullable=False, index=True),
    role = Column('role', Text, nullable=False),
    state = Column('state', Text, nullable=False),
    created = Column('created', DateTime, server_default=func.now(), nullable=False),
    last_modified = Column('last_modified', DateTime, server_onupdate=func.now(), nullable=False),
    closed = Column('closed', DateTime, nullable=True),

    def for_json(self, context):
        return table_dictize(self, context)

