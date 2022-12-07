from sqlalchemy import Table, Column, Integer, String, Text, MetaData, update
from sqlalchemy.sql import select, text
from sqlalchemy import func

import ckan.model as model
from ckan.lib.base import *

import logging

log = logging.getLogger(__name__)


class GeoserverRole():
    def __init__(self, id=None, user_id=None, role=None, state=None):
        self.id = id
        self.user_id = user_id
        self.role = role
        self.state = state

    def __eq__(self, other):
        if self.user_id == other.user_id and self.role == other.role:
            return True
        return False

    def is_active(self) -> bool:
        if self.state == 'Active':
            return True
        return False
    
    def _add(self):
        connection = model.Session.connection()
        try:
            connection.execute(
                text("""
                    INSERT INTO public.geoserver_role (user_id, role, state)
                    VALUES(:user_id, :role, :state)"""),
                    user_id=self.user_id, role=self.role, state=self.state)
            model.Session.commit()
        except Exception as e:
            log.error(e)
            raise Exception from(e)

    def _delete(self):
        connection = model.Session.connection()
        try:
            connection.execute(
                text("""UPDATE public.geoserver_role set "state" = 'Deleted'
                        WHERE id = :id"""),
                        id=self.id)
            model.Session.commit()
        except Exception as e:
            log.error(e)
            raise Exception from(e)

    def _make_active(self):
        connection = model.Session.connection()
        try:
            connection.execute(
                text("""UPDATE public.geoserver_role 
                        SET "state" = :state
                        WHERE id = :id"""),
                        id=self.id, state='Active')
            model.Session.commit()
        except Exception as e:
            log.error(e)
            raise Exception from(e)

    def save(self):
        existing = self.get_existing_roles()
        role_exists = len(existing) > 0
        if role_exists:
            existing[0]._make_active()
        else:
            self._add()

    def delete(self):
        if self.id is not None:
            self._delete()
        else:
            log.error('cannot delete role, role does exist.')

    def purge(self):
        connection = model.Session.connection()
        try:
            connection.execute(
                text("""
                    DELETE FROM public.geoserver_role
                    WHERE id = :id
                """), id=self.id)
            model.Session.commit()
        except Exception as e:
            log.error(e)
            raise Exception from(e)

    def get_existing_roles(self):
        connection = model.Session.connection()
        try:
            user_roles = connection.execute(
                text("""
                    SELECT * FROM public.geoserver_role 
                    WHERE user_id = :user_id 
                    AND role = :role 
                """), 
                user_id=self.user_id, role=self.role ).fetchall()
            return list(map(lambda role: GeoserverRole(*role), user_roles))
        except Exception as e:
            log.error(e)
            raise Exception from(e)
                        