from couchpotato.api import addApiView
from couchpotato.core.event import fireEvent, addEvent
from couchpotato.core.helpers.variable import mergeDicts, getImdb
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin

log = CPLog(__name__)


class Search(Plugin):

    def __init__(self):

        addApiView('search', self.search, docs = {
            'desc': 'Search the info in providers for a movie',
            'params': {
                'q': {'desc': 'The (partial) movie name you want to search for'},
                'type': {'desc': 'Search for a specific media type. Leave empty to search all.'},
            },
            'return': {'type': 'object', 'example': """{
    'success': True,
    'movies': array,
    'show': array,
    etc
}"""}
        })

        addEvent('app.load', self.addSingleSearches)

    def search(self, q = '', types = None, **kwargs):

        # Make sure types is the correct instance
        types = types or kwargs.get('type')
        if isinstance(types, str):
            types = [types]
        elif isinstance(types, (list, tuple, set)):
            types = list(types)

        imdb_identifier = getImdb(q)

        if not types:
            if imdb_identifier:
                result = fireEvent('movie.info', identifier = imdb_identifier, merge = True)
                if result and isinstance(result, dict) and (result.get('titles') or result.get('original_title') or result.get('imdb') or result.get('tmdb_id')):
                    media_type = result.get('type', 'movie')
                    result['type'] = media_type
                    result = {media_type: [result]}
                elif isinstance(result, list) and len(result) > 0:
                    media_type = 'movie'
                    for item in result:
                        if isinstance(item, dict):
                            media_type = item.get('type', media_type)
                            item['type'] = media_type
                    result = {media_type: result}
                else:
                    result = {}
            else:
                result = fireEvent('info.search', q = q, merge = True)
        else:
            result = {}
            for media_type in types:
                if imdb_identifier:
                    info = fireEvent('%s.info' % media_type, identifier = imdb_identifier, merge = True)
                    if info and isinstance(info, dict) and (info.get('titles') or info.get('original_title') or info.get('imdb') or info.get('tmdb_id')):
                        info['type'] = info.get('type', media_type)
                        result[media_type] = [info]
                    elif isinstance(info, list):
                        for item in info:
                            if isinstance(item, dict):
                                item['type'] = item.get('type', media_type)
                        result[media_type] = info
                    else:
                        result[media_type] = []
                else:
                    result[media_type] = fireEvent('%s.search' % media_type, q = q)

        return mergeDicts({
            'success': True,
        }, result)

    def createSingleSearch(self, media_type):

        def singleSearch(q, **kwargs):
            return self.search(q, type = media_type, **kwargs)

        return singleSearch

    def addSingleSearches(self):

        for media_type in fireEvent('media.types', merge = True):
            addApiView('%s.search' % media_type, self.createSingleSearch(media_type))
