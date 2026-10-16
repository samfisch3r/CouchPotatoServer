import re

from couchpotato.core.helpers.rss import RSS
from couchpotato.core.helpers.variable import tryInt, splitString
from couchpotato.core.logger import CPLog
from couchpotato.core.media.movie.providers.automation.base import Automation


log = CPLog(__name__)

autoload = 'CrowdAI'


class CrowdAI(Automation, RSS):

    interval = 1800

    def getIMDBids(self):

        movies = []

        urls = dict(zip(splitString(self.conf('automation_urls')), [tryInt(x) for x in splitString(self.conf('automation_urls_use'))]))

        for url in urls:

            if not urls[url]:
                continue

            rss_movies = self.getRSSData(url)

            for movie in rss_movies:

                description = self.getTextElement(movie, 'description')
                grabs = 0

                for item in movie:
                    if item.attrib.get('name') == 'grabs':
                        grabs = item.attrib.get('value')
                        break

                if int(grabs) > tryInt(self.conf('number_grabs')):
                    title = re.match(r'.*Title: .a href.*/">(.*) \(\d{4}\).*', description).group(1)
                    log.info2('%s grabs for movie: %s, enqueue...', (grabs, title))
                    year = re.match(r'.*Year: (\d{4}).*', description).group(1)
                    imdb = self.search(title, year)

                    if imdb and self.isMinimalMovie(imdb):
                        movies.append(imdb['imdb'])

    def isDisabled(self):
        return True

    def getIMDBids(self):
        return []


config = []
