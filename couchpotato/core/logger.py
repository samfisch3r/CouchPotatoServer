import logging
import re


class CPLog(object):

    context = ''
    replace_private = ['api', 'apikey', 'api_key', 'password', 'username', 'h', 'uid', 'key', 'passkey']

    Env = None
    is_develop = False

    def __init__(self, context = ''):
        if context.endswith('.main'):
            context = context[:-5]

        self.context = context
        self.logger = logging.getLogger()

    def setup(self):

        if not self.Env:
            from couchpotato.environment import Env

            self.Env = Env
            self.is_develop = Env.get('dev')

            from couchpotato.core.event import addEvent
            addEvent('app.after_shutdown', self.close)

    def close(self, *args, **kwargs):
        logging.shutdown()

    def _parse_args(self, args):
        if not args:
            return ()
        if len(args) == 1 and isinstance(args[0], (tuple, dict)):
            return args[0]
        return args

    def info(self, msg, *args):
        self.logger.info(self.addContext(msg, self._parse_args(args)))

    def info2(self, msg, *args):
        self.logger.log(19, self.addContext(msg, self._parse_args(args)))

    def debug(self, msg, *args):
        self.logger.debug(self.addContext(msg, self._parse_args(args)))

    def error(self, msg, *args):
        self.logger.error(self.addContext(msg, self._parse_args(args)))

    def warning(self, msg, *args):
        self.logger.warning(self.addContext(msg, self._parse_args(args)))

    def critical(self, msg, *args):
        self.logger.critical(self.addContext(msg, self._parse_args(args)), exc_info = 1)

    def addContext(self, msg, replace_tuple = ()):
        return '[%+25.25s] %s' % (self.context[-25:], self.safeMessage(msg, replace_tuple))

    def safeMessage(self, msg, replace_tuple = ()):

        from couchpotato.core.helpers.encoding import toUnicode

        msg = toUnicode(msg)

        try:
            if isinstance(replace_tuple, tuple):
                msg = msg % tuple([toUnicode(x) if not isinstance(x, (int, float)) else x for x in replace_tuple])
            elif isinstance(replace_tuple, dict):
                msg = msg % dict((k, toUnicode(v) if not isinstance(v, (int, float)) else v) for k, v in replace_tuple.items())
            else:
                msg = msg % toUnicode(replace_tuple)
        except Exception as e:
            self.logger.error('Failed encoding stuff to log "%s": %s' % (msg, e))

        self.setup()
        if not self.is_develop:

            for replace in self.replace_private:
                msg = re.sub(r'(\?%s=)[^&]+' % replace, '?%s=xxx' % replace, msg)
                msg = re.sub(r'(&%s=)[^&]+' % replace, '&%s=xxx' % replace, msg)

            # Replace api key
            try:
                api_key = self.Env.setting('api_key')
                if api_key:
                    msg = msg.replace(api_key, 'API_KEY')
            except:
                pass

        return toUnicode(msg)
