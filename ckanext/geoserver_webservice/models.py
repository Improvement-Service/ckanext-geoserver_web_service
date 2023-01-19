from sqlalchemy.sql import text
import ckan.model as model
from ckan.lib.base import *
import datetime
import ckan.model as model
import logging
log = logging.getLogger(__name__)

class GeoserverRole():
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.role = kwargs.get('role')
        self.state = kwargs.get('state', 'Active')
        self.created = kwargs.get('created')
        self.last_modified = kwargs.get('last_modified')
        self.closed = kwargs.get('closed')

    def __eq__(self, other):
        if self.user_id == other.user_id and self.role == other.role:
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
            log.error(e, exc_info=True)
            raise Exception from(e)
    
    def change_state(self, state):
        last_modified=datetime.datetime.now()
        closed = None if state == 'Active' else last_modified
        connection = model.Session.connection()
        try:
            connection.execute(
                text("""UPDATE public.geoserver_role 
                        SET "state" = :state, 
                        "last_modified" = :last_modified, 
                        "closed" = :closed
                        WHERE id = :id"""),
                        id=self.id,
                        state=state,
                        last_modified=last_modified,
                        closed=closed)
            model.Session.commit()
        except Exception as e:
            log.error(e)
            raise Exception from(e)

    def save(self):
        existing = self.get_existing_roles()
        role_exists = len(existing) > 0
        if role_exists:
            existing[0].change_state('Active')
        else:
            self._add()

    def delete(self):
        if self.id is not None:
            self.change_state('Deleted')
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
            return list(map(lambda role: GeoserverRole(**role), user_roles))
        except Exception as e:
            log.error(e)
            raise Exception from(e)
                        