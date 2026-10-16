import traceback

from bs4 import BeautifulSoup
from couchpotato import fireEvent
from couchpotato.core.helpers.rss import RSS
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.media.movie.providers.automation.base import Automation


log = CPLog(__name__)

autoload = 'Bluray'


class Bluray(Automation, RSS):

    interval = 1800
    rss_url = 'http://www.blu-ray.com/rss/newreleasesfeed.xml'
    backlog_url = 'http://www.blu-ray.com/movies/movies.php?show=newreleases&page=%s'
    display_url = 'http://www.blu-ray.com/movies/movies.php?show=newreleases'
    chart_order = 1

    def getIMDBids(self):

        movies = []

        if self.conf('backlog'):

            cookie = {'Cookie': 'listlayout_7=full'}
            page = 0
            while True:
                page += 1

                url = self.backlog_url % page
                data = self.getHTMLData(url, headers = cookie)
                soup = BeautifulSoup(data)

                try:
                    # Stop if the release year is before the minimal year
                    brk = False
                    h3s = soup.body.find_all('h3')
                    for h3 in h3s:
                        if h3.parent.name != 'a':

                            try:
                                page_year = tryInt(h3.get_text()[-4:])
                                if page_year > 0 and page_year < self.getMinimal('year'):
                                    brk = True
                            except:
                                log.error('Failed determining page year: %s', traceback.format_exc())
                                brk = True
                                break

                    if brk:
                        break

                    for h3 in h3s:
                        try:
                            if h3.parent.name == 'a':
                                name = h3.get_text().lower().split('blu-ray')[0].strip()

                                if not name.find('/') == -1:  # make sure it is not a double movie release
                                    continue

                                if not h3.parent.parent.small:  # ignore non-movie tables
                                    continue

                                year = h3.parent.parent.small.get_text().split('|')[1].strip()

                                if tryInt(year) < self.getMinimal('year'):
                                    continue

                                imdb = self.search(name, year)

                                if imdb:
                                    if self.isMinimalMovie(imdb):
                                        movies.append(imdb['imdb'])
                        except:
                            log.debug('Error parsing movie html: %s', traceback.format_exc())
                            break
                except:
                    log.debug('Error loading page %s: %s', (page, traceback.format_exc()))
                    break

            self.conf('backlog', value = False)

        rss_movies = self.getRSSData(self.rss_url)

        for movie in rss_movies:
            name = self.getTextElement(movie, 'title').lower().split('blu-ray')[0].strip('(').rstrip()
            year = self.getTextElement(movie, 'description').split('|')[1].strip('(').strip()

            if not name.find('/') == -1:  # make sure it is not a double movie release
                continue

            if tryInt(year) < self.getMinimal('year'):
                continue

            imdb = self.search(name, year)

            if imdb:
                if self.isMinimalMovie(imdb):
    def isDisabled(self):
        return True

    def getIMDBids(self):
        return []

    def getChartList(self):
        return []


config = []
