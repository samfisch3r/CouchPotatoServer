from couchpotato import fireEvent
from couchpotato.core.logger import CPLog
from couchpotato.core.media.movie.providers.automation.base import Automation

log = CPLog(__name__)

autoload = 'PopularMovies'


class PopularMovies(Automation):

    interval = 1800
    url = 'https://s3.amazonaws.com/popular-movies/movies.json'

    def getIMDBids(self):

        movies = []
        retrieved_movies = self.getJsonData(self.url)

        if retrieved_movies:
            for movie in retrieved_movies:
                imdb_id = movie.get('imdb_id')
                info = fireEvent('movie.info', identifier = imdb_id, extended = False, merge = True)
                if self.isMinimalMovie(info):
                    movies.append(imdb_id)

    def isDisabled(self):
        return True

    def getIMDBids(self):
        return []


config = []
