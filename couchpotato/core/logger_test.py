import unittest
from couchpotato.core.logger import CPLog


class LoggerTest(unittest.TestCase):

    def test_cplog_accepts_tuples_and_varargs(self):
        log = CPLog('test')
        # Standard tuple
        msg = log.safeMessage('Hello %s %s', ('world', 123))
        self.assertIn('Hello world 123', msg)

        # Varargs via _parse_args
        parsed_args = log._parse_args(('world', 123))
        msg = log.safeMessage('Hello %s %s', parsed_args)
        self.assertIn('Hello world 123', msg)

        # Single tuple passed to _parse_args
        parsed_tuple = log._parse_args((('world', 123),))
        self.assertEqual(parsed_tuple, ('world', 123))

        # Dict passed to _parse_args
        parsed_dict = log._parse_args(({'name': 'CP'},))
        self.assertEqual(parsed_dict, {'name': 'CP'})

        # No args
        self.assertEqual(log._parse_args(()), ())


if __name__ == '__main__':
    unittest.main()
