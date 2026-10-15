import unittest
from unittest import mock
from requests import HTTPError, Response

from couchpotato.core.media._base.providers.nzb.newznab import Base as NewznabProvider


class NewznabProviderTest(unittest.TestCase):

    def setUp(self):
        self.provider = NewznabProvider.__new__(NewznabProvider)
        self.provider.config = {}
        self.provider.limits_reached = {}

    def _mock_conf(self, key):
        config_values = {
            'enabled': True,
            'use': '1,0',
            'host': 'https://api.nzbgeek.info,https://api.dognzb.cr',
            'api_key': 'key_geek,key_dog',
            'extra_score': '10,0',
            'custom_tag': 'rls=1,',
            'custom_categories': '2000,2000',
        }
        return config_values.get(key)

    @mock.patch.object(NewznabProvider, 'conf')
    def test_get_hosts_parses_comma_separated_values(self, mock_conf):
        mock_conf.side_effect = self._mock_conf
        hosts = self.provider.getHosts()

        self.assertEqual(len(hosts), 2)
        self.assertEqual(hosts[0]['host'], 'https://api.nzbgeek.info')
        self.assertEqual(hosts[0]['api_key'], 'key_geek')
        self.assertEqual(hosts[0]['use'], '1')
        self.assertEqual(hosts[0]['extra_score'], 10)
        self.assertEqual(hosts[0]['custom_tag'], 'rls=1')

        self.assertEqual(hosts[1]['host'], 'https://api.dognzb.cr')
        self.assertEqual(hosts[1]['use'], '0')

    @mock.patch.object(NewznabProvider, 'conf')
    def test_is_enabled(self, mock_conf):
        mock_conf.side_effect = self._mock_conf
        with mock.patch('couchpotato.core.media._base.providers.nzb.base.NZBProvider.isEnabled', return_value=True):
            self.assertTrue(self.provider.isEnabled())

            hosts = self.provider.getHosts()
            self.assertTrue(self.provider.isEnabled(hosts[0]))
            self.assertFalse(self.provider.isEnabled(hosts[1]))

    def test_build_details_url(self):
        query = self.provider.buildDetailsUrl('item123', 'test_key')
        self.assertIn('t=details', query)
        self.assertIn('id=item123', query)
        self.assertIn('apikey=test_key', query)

    @mock.patch.object(NewznabProvider, 'urlopen')
    def test_download_success(self, mock_urlopen):
        mock_urlopen.return_value = b'<?xml><nzb>content</nzb>'
        url = 'https://api.nzbgeek.info/api?t=get&id=123&apikey=key_geek'

        data = self.provider.download(url=url, nzb_id='123')
        self.assertEqual(data, b'<?xml><nzb>content</nzb>')
        self.assertFalse(self.provider.limits_reached.get('api.nzbgeek.info'))

    @mock.patch.object(NewznabProvider, 'urlopen')
    def test_download_handles_http_429_rate_limit_without_read_error(self, mock_urlopen):
        # Create a mock requests HTTPError with response
        response = Response()
        response.status_code = 429
        response._content = b'Download limit reached'
        error = HTTPError(response=response)
        mock_urlopen.side_effect = error

        url = 'https://api.nzbgeek.info/api?t=get&id=123&apikey=key_geek'
        result = self.provider.download(url=url, nzb_id='123')

        self.assertEqual(result, 'try_next')
        self.assertIn('api.nzbgeek.info', self.provider.limits_reached)
        self.assertNotEqual(self.provider.limits_reached['api.nzbgeek.info'], False)
