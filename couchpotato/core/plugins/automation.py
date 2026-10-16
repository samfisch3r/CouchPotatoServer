from couchpotato.api import addApiView
from couchpotato.core.event import addEvent, fireEvent
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin
from couchpotato.environment import Env

log = CPLog(__name__)

autoload = 'Automation'


class Automation(Plugin):

    def __init__(self):
        pass

    def setCrons(self):
        pass

    def addMoviesFromApi(self, **kwargs):
        return {
            'success': True
        }

    def addMovies(self):
        return True

    def isDisabled(self):
        return True


config = []
