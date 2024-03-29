from __future__ import absolute_import

import datetime
import logging

from sqlalchemy import Table, Column, Integer, Text, MetaData, DateTime, ForeignKey, types
from sqlalchemy.sql import select, text, func
from ckan.lib.dictization import table_dictize
from ckan.model import types as _types
from ckan.model import meta, core, domain_object, User
import ckan.model as model
import warnings

from .base import Base

log = logging.getLogger(__name__)

class GeoserverUserRoleModel(Base, domain_object.DomainObject):
    __tablename__ = 'geoserver_user_role'

    id = Column('id', types.UnicodeText, primary_key=True, nullable=False, index=True, default=_types.make_uuid)
    user_id = Column('user_id', types.UnicodeText, ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True)
    role = Column('role', Text, nullable=False)
    state = Column('state', types.UnicodeText, default=core.State.ACTIVE)
    created = Column('created', DateTime, default=datetime.datetime.now, nullable=False)
    last_modified = Column('last_modified', DateTime, default=datetime.datetime.now, nullable=False)
    closed = Column('closed', DateTime, nullable=True)

    def __init__(self, **kw):
        super(GeoserverUserRoleModel, self).__init__(**kw)

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
        query = self.Session.query(GeoserverUserRoleModel)
        query = query.filter(
            GeoserverUserRoleModel.user_id == self.user_id, 
            GeoserverUserRoleModel.role == self.role,
            GeoserverUserRoleModel.state == core.State.ACTIVE
            )
        role = query.first()
        if role is None:
            super(GeoserverUserRoleModel, self).add(**kw)

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


class GeoserverOrganizationRoleModel(Base, domain_object.DomainObject):
    __tablename__ = 'geoserver_organization_role'

    id = Column('id', types.UnicodeText, primary_key=True, nullable=False, index=True, default=_types.make_uuid)
    organization_id = Column('organization_id', types.UnicodeText, ForeignKey("group.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True)
    role = Column('role', Text, nullable=False)
    state = Column('state', types.UnicodeText, default=core.State.ACTIVE)
    created = Column('created', DateTime, default=datetime.datetime.now, nullable=False)
    last_modified = Column('last_modified', DateTime, default=datetime.datetime.now, nullable=False)
    closed = Column('closed', DateTime, nullable=True)

    def __init__(self, **kw):
        super(GeoserverOrganizationRoleModel, self).__init__(**kw)

    def for_json(self, context):
        return table_dictize(self, context)

    @classmethod
    def get_organization_roles(cls, organization_id: str):
        query = cls.Session.query(cls).autoflush(False)
        query = query.filter(cls.organization_id == organization_id)
        return query.all()
    
    @classmethod
    def get_organizations_roles(cls, organization_ids: list):
        query = cls.Session.query(cls).autoflush(False)
        query = query.filter(cls.organization_id.in_(organization_ids))
        return query.all()

    @classmethod
    def get(cls, role_id):
        query = cls.Session.query(cls).autoflush(False)
        query = query.filter(cls.id == role_id)
        return query.first()

    def add(self, **kw):
        query = self.Session.query(GeoserverOrganizationRoleModel)
        query = query.filter(
            GeoserverOrganizationRoleModel.organization_id == self.organization_id, 
            GeoserverOrganizationRoleModel.role == self.role,
            GeoserverOrganizationRoleModel.state == core.State.ACTIVE
            )
        role = query.first()
        if role is None:
            super(GeoserverOrganizationRoleModel, self).add(**kw)

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
    
class GeoserverUserAuthkey(Base, domain_object.DomainObject):
    __tablename__ = 'geoserver_user_authkey'

    authkey = Column('authkey', types.UnicodeText, primary_key=True, nullable=False, index=True, default=_types.make_uuid)
    user_id = Column('user_id', types.UnicodeText, ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE") , index=True)
    state = Column('state', types.UnicodeText, default=core.State.ACTIVE)
    created = Column('created', DateTime, default=datetime.datetime.now, nullable=False)
    last_access = Column('last_access', DateTime, nullable=True)
    closed = Column('closed', DateTime, nullable=True)

    def __init__(self, **kw):
        super(GeoserverUserAuthkey, self).__init__(**kw)

    def for_json(self, context):
        return table_dictize(self, context)

    
    @classmethod
    def get(cls, authkey):
        query = cls.Session.query(cls).autoflush(False)
        query = query.filter(cls.authkey == authkey)
        return query.first()

    @classmethod
    def get_user_from_authkey(cls, authkey):
        geoserver_user_authkey = cls.get(authkey=authkey)
        if geoserver_user_authkey and geoserver_user_authkey.state == core.State.ACTIVE:
            geoserver_user_authkey.update_last_accessed()
            user = model.User.get(geoserver_user_authkey.user_id)
            if user and user.state == core.State.ACTIVE:
                return user
            else:
                geoserver_user_authkey.make_deleted()
    
    @classmethod
    def get_geoserver_user_authkey_for_user(cls, user_id):
        user = model.User.get(user_id)
        if user:
            query = cls.Session.query(cls).autoflush(False)
            query = query.filter(cls.user_id == user.id, cls.state == core.State.ACTIVE)
            geoserver_user_authkey = query.first()
            if geoserver_user_authkey is not None:
                return geoserver_user_authkey
            else:
                GeoserverUserAuthkey(user_id=user.id).save()
                return query.first()
    
    @classmethod
    def generate_new_user_authkey(cls, user_id):
        user = model.User.get(user_id)
        if user:
            query = cls.Session.query(cls).autoflush(False)
            query = query.filter(cls.user_id == user.id, cls.state == core.State.ACTIVE)
            geoserver_user_authkey = query.first()
            if geoserver_user_authkey is not None:
                geoserver_user_authkey.make_deleted()
                GeoserverUserAuthkey(user_id=user.id).save()
                return query.first()
            else:
                GeoserverUserAuthkey(user_id=user.id).save()
                return query.first()

    def add(self, **kw):
        query = self.Session.query(GeoserverUserAuthkey)
        query = query.filter(
            GeoserverUserAuthkey.user_id == self.user_id, 
            GeoserverUserAuthkey.state == core.State.ACTIVE #uncomment to add new role each time to keep history.
            )
        role = query.first()
        if role is None:
            super(GeoserverUserAuthkey, self).add(**kw)
    
    @classmethod
    def add_for_all_users(cls):
        sql = cls.Session.query(model.User).filter_by(state=core.State.ACTIVE)
        result = cls.Session.execute(sql).fetchall()
        for user in result:
            GeoserverUserAuthkey(user_id=user.user_id).save()

    def update_last_accessed(self):
        self.last_access = datetime.datetime.now()
        self.save()

    def _change_state(self, state):
        self.closed = None if state == core.State.ACTIVE else datetime.datetime.now()
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
