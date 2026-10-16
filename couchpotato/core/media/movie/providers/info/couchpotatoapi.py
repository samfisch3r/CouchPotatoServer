from couchpotato.core.event import addEvent
from couchpotato.core.logger import CPLog
from couchpotato.core.media.movie.providers.base import MovieProvider


log = CPLog(__name__)

autoload = 'CouchPotatoApi'


class CouchPotatoApi(MovieProvider):

    urls = {}
    http_time_between_calls = 0
    api_version = 1

    def __init__(self):
        addEvent('movie.info', self.getInfo, priority = 2)
        addEvent('movie.info.release_date', self.getReleaseDate)

        addEvent('info.search', self.search, priority = 1)
        addEvent('movie.search', self.search, priority = 1)

        addEvent('movie.suggest', self.getSuggestions)
        addEvent('movie.is_movie', self.isMovie)

        addEvent('release.validate', self.validate)

        addEvent('cp.api_call', self.call)

        addEvent('cp.source_url', self.getSourceUrl)
        addEvent('cp.messages', self.getMessages)

    def isDisabled(self):
        return True

    def call(self, url, **kwargs):
        return []

    def getMessages(self, last_check = 0):
        return []

    def getSourceUrl(self, repo = None, repo_name = None, branch = None):
        return None

    def search(self, q, limit = 5):
        return []

    def validate(self, name = None):
        return None

    def isMovie(self, identifier = None, adding = False, **kwargs):
        return True

    def getInfo(self, identifier = None, adding = False, **kwargs):
        return {}

    def getReleaseDate(self, identifier = None):
        return {}

    def getSuggestions(self, movies = None, ignore = None):
        return []

    def getRequestHeaders(self):
        return {}


config = [{
    'name': 'couchpotatoapi',
    'groups': [
        {
            'tab': 'providers',
            'name': 'couchpotatoapi',
            'label': 'CouchPotato API',
            'description': 'Legacy CouchPotato central API service (defunct).',
            'wizard': False,
            'options': [
                {
                    'name': 'enabled',
                    'default': False,
                    'type': 'enabler',
                },
            ],
        },
    ],
}]
