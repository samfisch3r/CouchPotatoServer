from hashlib import md5

from CodernityDB.hash_index import HashIndex


class QualityIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(QualityIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return md5(key.encode('utf-8') if isinstance(key, str) else key).hexdigest()

    def make_key_value(self, data):
        if data.get('_t') == 'quality' and data.get('identifier'):
            identifier = data.get('identifier')
            return md5(identifier.encode('utf-8') if isinstance(identifier, str) else identifier).hexdigest(), None
