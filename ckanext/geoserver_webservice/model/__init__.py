from __future__ import absolute_import

import datetime
import logging

from sqlalchemy import Table, Column, Integer, Text, MetaData, update, DateTime, ForeignKey, types
from sqlalchemy.sql import select, text, func
from ckan.lib.dictization import table_dictize
from ckan.model import types as _types
from ckan.model import meta, core, domain_object

from .base import Base

log = logging.getLogger(__name__)


# geoserver_role_table = Table(
#                             'geoserver_role', meta.metadata,
#                             Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
#                             Column('user_id', types.UnicodeText, ForeignKey("user.id")),
#                             Column('role', Text,  nullable=False),
#                             Column('state', Text, nullable=False, default=core.State.ACTIVE),
#                             Column('created', DateTime, default=datetime.datetime.utcnow),
#                             Column('last_modified', DateTime, default=datetime.datetime.utcnow),
#                             Column('closed', DateTime),
#                         )

class GeoserverRoleModel(Base, domain_object.DomainObject):
    __tablename__ = 'geoserver_role'

    id = Column('id', types.UnicodeText, primary_key=True, nullable=False, index=True, default=_types.make_uuid)
    user_id = Column('user_id', types.UnicodeText, ForeignKey("user.id"), index=True)
    role = Column('role', Text, nullable=False)
    state = Column('state', types.UnicodeText, default=core.State.ACTIVE)
    created = Column('created', DateTime, default=datetime.datetime.now, nullable=False)
    last_modified = Column('last_modified', DateTime, default=datetime.datetime.now, nullable=False)
    closed = Column('closed', DateTime, nullable=True)

    def __init__(self, **kw):
        super(GeoserverRoleModel, self).__init__(**kw)

    def for_json(self, context):
        return table_dictize(self, context)

    @classmethod
    def get_user_roles(cls, user_id):
        query = cls.Session.query(cls).autoflush(False)
        query = query.filter(cls.user_id == user_id)
        return query.all()

    @classmethod
    def get(cls, role_id):
        query = cls.Session.query(cls).autoflush(False)
        query = query.filter(cls.id == role_id)
        return query.first()

    def add(self, **kw):
        query = self.Session.query(GeoserverRoleModel)
        query = query.filter(
            GeoserverRoleModel.user_id == self.user_id, 
            GeoserverRoleModel.role == self.role,
            # GeoserverRoleModel.state == core.State.ACTIVE #uncomment to add new role each time to keep history.
            )
        role = query.first()
        if role is None:
            super(GeoserverRoleModel, self).add(**kw)
        else:
            if role.state != self.state:
                if self.state == core.State.DELETED:
                    role._change_state(core.State.DELETED)
                else:
                    role._change_state(core.State.ACTIVE)
            
    def _change_state(self, state):
        self.last_modified=datetime.datetime.now()
        self.closed = None if state == core.State.ACTIVE else self.last_modified
        self.state = state
        self.save()

    def make_active(self):
        self._change_state(core.State.ACTIVE)
    
    def make_deleted(self):
        self._change_state(core.State.DELETED)

    def purge(self):
        try:
            self.delete()
            self.commit()
        except Exception as e:
            log.error(e, exc_info=True)
            raise Exception from(e)
    
    @classmethod
    def purge_deleted(cls):
        query = cls.Session.query(cls).autoflush(False)
        query = query.filter(cls.state == core.State.DELETED)
        purgeable_roles = query.all()
        for purgeable_role in purgeable_roles:
            purgeable_role.purge()


    

