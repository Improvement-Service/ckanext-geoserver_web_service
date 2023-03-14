import logging
import click
from ckanext.geoserver_webservice.dbutil import init_tables
from ckan.lib.cli import CkanCommand

log = logging.getLogger(__name__)

class InitDB(CkanCommand):
    """Initialise database tables"""

    def command(self):
        self._load_config()
        init_tables()
        log.info("Set up statistics tables in main database")
