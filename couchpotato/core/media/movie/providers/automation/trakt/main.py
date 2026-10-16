from couchpotato import Env
from couchpotato.api import addApiView
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.base import Provider
from couchpotato.core.media.movie.providers.automation.base import Automation


log = CPLog(__name__)


class TraktBase(Provider):

    client_id = '8a54ed7b5e1b56d874642770ad2e8b73e2d09d6e993c3a92b1e89690bb1c9014'
    api_url = 'https://api-v2launch.trakt.tv/'

    def call(self, method_url, post_data = None):
        return []


class Trakt(Automation, TraktBase):

    urls = {
        'watchlist': 'sync/watchlist/movies?extended=full',
        'oauth': '',
        'refresh_token': '',
    }

    def __init__(self):
        super(Trakt, self).__init__()
        addApiView('automation.trakt.auth_url', self.getAuthorizationUrl)
        addApiView('automation.trakt.credentials', self.getCredentials)

    def isDisabled(self):
        return True

    def getIMDBids(self):
        return []

    def getWatchlist(self):
        return []

    def getAuthorizationUrl(self, host = None, **kwargs):
        return {
            'success': False,
            'message': 'Trakt automation is disabled.',
        }

    def getCredentials(self, **kwargs):
        return 'redirect', Env.get('web_base')
