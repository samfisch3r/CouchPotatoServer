import datetime
import traceback
from CodernityDB.database import RecordNotFound
from couchpotato import Env, get_db
from couchpotato.core.helpers.variable import getTitle, splitString

from couchpotato.core.logger import CPLog
from couchpotato.api import addApiView
from couchpotato.core.event import fireEvent
from couchpotato.core.plugins.base import Plugin


log = CPLog(__name__)


class Charts(Plugin):

    def __init__(self):
        addApiView('charts.view', self.automationView)
        addApiView('charts.ignore', self.ignoreView)

    def getTmdbCharts(self, force_update = False):

        cache_key = 'charts.tmdb.theaters_and_digital'
        if not force_update:
            cached = self.getCache(cache_key)
            if cached:
                return cached

        charts = []
        try:
            from couchpotato.core.media.movie.providers.info.themoviedb import TheMovieDb

            tmdb = TheMovieDb()
            api_key = tmdb.getApiKey()
            if not api_key:
                return []

            # 1. In Theaters
            now_playing_url = 'https://api.themoviedb.org/3/movie/now_playing?api_key=%s&language=en-US&page=1' % api_key
            raw_theaters = tmdb.getJsonData(now_playing_url, show_error = False)
            theater_results = (raw_theaters.get('results') or [])[:12] if isinstance(raw_theaters, dict) else []

            theater_movies = []
            for item in theater_results:
                tmdb_id = item.get('id')
                if not tmdb_id: continue
                det_url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (tmdb_id, api_key)
                det = tmdb.getJsonData(det_url, show_error = False)
                imdb_id = det.get('imdb_id') if isinstance(det, dict) else None
                if not imdb_id: continue
                poster_path = item.get('poster_path')
                poster_url = 'https://image.tmdb.org/t/p/w300%s' % poster_path if poster_path else None
                theater_movies.append({
                    'title': item.get('title'),
                    'titles': [item.get('title')],
                    'year': str(item.get('release_date') or '')[:4],
                    'imdb': imdb_id,
                    'tmdb_id': tmdb_id,
                    'plot': item.get('overview'),
                    'images': {'poster': [poster_url] if poster_url else []}
                })

            if theater_movies:
                charts.append({
                    'name': 'In Theaters',
                    'url': 'https://www.themoviedb.org/movie/now-playing',
                    'order': 1,
                    'list': theater_movies
                })

            # 2. Digital & Streaming Releases (New releases from studios that don't release in theater)
            today = datetime.date.today()
            start = today - datetime.timedelta(days = 90)
            discover_url = ('https://api.themoviedb.org/3/discover/movie?api_key=%s&language=en-US'
                            '&sort_by=popularity.desc&with_release_type=4'
                            '&primary_release_date.gte=%s&primary_release_date.lte=%s'
                            '&vote_count.gte=10&page=1') % (api_key, str(start), str(today))
            raw_digital = tmdb.getJsonData(discover_url, show_error = False)
            digital_results = (raw_digital.get('results') or [])[:12] if isinstance(raw_digital, dict) else []

            digital_movies = []
            for item in digital_results:
                tmdb_id = item.get('id')
                if not tmdb_id: continue
                det_url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (tmdb_id, api_key)
                det = tmdb.getJsonData(det_url, show_error = False)
                imdb_id = det.get('imdb_id') if isinstance(det, dict) else None
                if not imdb_id: continue
                poster_path = item.get('poster_path')
                poster_url = 'https://image.tmdb.org/t/p/w300%s' % poster_path if poster_path else None
                digital_movies.append({
                    'title': item.get('title'),
                    'titles': [item.get('title')],
                    'year': str(item.get('release_date') or '')[:4],
                    'imdb': imdb_id,
                    'tmdb_id': tmdb_id,
                    'plot': item.get('overview'),
                    'images': {'poster': [poster_url] if poster_url else []}
                })

            if digital_movies:
                charts.append({
                    'name': 'Digital & Streaming Releases',
                    'url': 'https://www.themoviedb.org/discover/movie',
                    'order': 2,
                    'list': digital_movies
                })

            if charts:
                self.setCache(cache_key, charts, timeout = 86400)

        except:
            log.error('Failed fetching TMDB charts: %s', traceback.format_exc())

        return charts

    def automationView(self, force_update = False, **kwargs):

        db = get_db()

        charts = self.getTmdbCharts(force_update = force_update)
        ignored = splitString(Env.prop('charts_ignore', default = ''))

        # Create a list the movie/list.js can use
        for chart in charts:
            medias = []
            for media in chart.get('list', []):

                identifier = media.get('imdb')
                if identifier in ignored:
                    continue

                try:
                    try:
                        in_library = db.get('media', 'imdb-%s' % identifier)
                        if in_library:
                            continue
                    except RecordNotFound:
                        pass
                except:
                    pass

                # Cache poster
                posters = media.get('images', {}).get('poster', [])
                poster = [x for x in posters if 'tmdb' in x]
                posters = poster if len(poster) > 0 else posters

                cached_poster = fireEvent('file.download', url = posters[0], single = True) if len(posters) > 0 else False
                files = {'image_poster': [cached_poster] } if cached_poster else {}

                medias.append({
                    'status': 'chart',
                    'title': getTitle(media),
                    'type': 'movie',
                    'info': media,
                    'files': files,
                    'identifiers': {
                        'imdb': identifier
                    }
                })

            chart['list'] = medias

        return {
            'success': True,
            'count': len(charts),
            'charts': charts,
            'ignored': ignored,
        }

    def ignoreView(self, imdb = None, **kwargs):

        ignored = splitString(Env.prop('charts_ignore', default = ''))

        if imdb:
            ignored.append(imdb)
            Env.prop('charts_ignore', ','.join(set(ignored)))

        return {
            'result': True
        }
