from string import ascii_letters, digits
from urllib.parse import quote_plus
import os
import re
import traceback
import unicodedata

from chardet import detect
from couchpotato.core.logger import CPLog


log = CPLog(__name__)


def toSafeString(original):
    valid_chars = "-_.() %s%s" % (ascii_letters, digits)
    cleaned_filename = unicodedata.normalize('NFKD', toUnicode(original))
    valid_string = ''.join(c for c in cleaned_filename if c in valid_chars)
    return ' '.join(valid_string.split())


def simplifyString(original):
    string = stripAccents(original.lower())
    string = toSafeString(' '.join(re.split(r'\W+', string)))
    split = re.split(r'\W+|_', string.lower())
    return toUnicode(' '.join(split))


def toUnicode(original, *args):
    try:
        if isinstance(original, str):
            return original
        if isinstance(original, bytes):
            try:
                from couchpotato.environment import Env
                return original.decode(Env.get("encoding"))
            except:
                try:
                    detected = detect(original)
                    if detected.get('confidence') > 0.8:
                        return original.decode(detected.get('encoding'))
                except:
                    pass

                return original.decode('utf-8', 'replace')
        else:
            return str(original, *args)
    except:
        log.error('Unable to decode value "%s..." : %s ', (repr(original)[:20], traceback.format_exc()))
        return 'ERROR DECODING STRING'


def ss(original, *args):
    return toUnicode(original, *args)


def sp(path, *args):

    # Standardise encoding, normalise case, path and strip trailing '/' or '\'
    if not path or len(path) == 0:
        return path

    # convert windows path (from remote box) to *nix path
    if os.path.sep == '/' and '\\' in path:
        path = '/' + path.replace(':', '').replace('\\', '/')

    path = os.path.normpath(toUnicode(path, *args))

    # Remove any trailing path separators
    if path != os.path.sep:
        path = path.rstrip(os.path.sep)

    # Add a trailing separator in case it is a root folder on windows (crashes guessit)
    if len(path) == 2 and path[1] == ':':
        path = path + os.path.sep

    # Replace *NIX ambiguous '//' at the beginning of a path with '/' (crashes guessit)
    path = re.sub('^//', '/', path)

    return path


def ek(original, *args):
    if isinstance(original, bytes):
        try:
            from couchpotato.environment import Env
            return original.decode(Env.get('encoding'), 'ignore')
        except UnicodeDecodeError:
            raise

    return original


def isInt(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def stripAccents(s):
    return ''.join((c for c in unicodedata.normalize('NFD', toUnicode(s)) if unicodedata.category(c) != 'Mn'))


def tryUrlencode(s):
    new = ''
    if isinstance(s, dict):
        for key, value in s.items():
            new += '&%s=%s' % (key, tryUrlencode(value))

        return new[1:]
    else:
        for letter in ss(s):
            try:
                new += quote_plus(letter)
            except:
                new += letter

    return new
