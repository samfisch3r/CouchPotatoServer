from hashlib import md5

from CodernityDB.hash_index import HashIndex
from CodernityDB.tree_index import TreeBasedIndex


class ReleaseIndex(TreeBasedIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ReleaseIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'release' and data.get('media_id'):
            return data['media_id'], None


class ReleaseStatusIndex(TreeBasedIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ReleaseStatusIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return md5(key.encode('utf-8') if isinstance(key, str) else key).hexdigest()

    def make_key_value(self, data):
        if data.get('_t') == 'release' and data.get('status'):
            status = data.get('status')
            return md5(status.encode('utf-8') if isinstance(status, str) else status).hexdigest(), {'media_id': data.get('media_id')}


class ReleaseIDIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ReleaseIDIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return md5(key.encode('utf-8') if isinstance(key, str) else key).hexdigest()

    def make_key_value(self, data):
        if data.get('_t') == 'release' and data.get('identifier'):
            identifier = data.get('identifier')
            return md5(identifier.encode('utf-8') if isinstance(identifier, str) else identifier).hexdigest(), {'media_id': data.get('media_id')}


class ReleaseDownloadIndex(HashIndex):
    _version = 2

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ReleaseDownloadIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        key = key.lower()
        return md5(key.encode('utf-8') if isinstance(key, str) else key).hexdigest()

    def make_key_value(self, data):
        if data.get('_t') == 'release' and data.get('download_info') and data['download_info']['id'] and data['download_info']['downloader']:
            key = ('%s-%s' % (data['download_info']['downloader'], data['download_info']['id'])).lower()
            return md5(key.encode('utf-8')).hexdigest(), None
