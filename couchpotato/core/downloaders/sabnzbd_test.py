import json
import unittest
from unittest import mock

from couchpotato.core.downloaders.sabnzbd import Sabnzbd


class SabnzbdDownloaderTest(unittest.TestCase):

    def setUp(self):
        self.downloader = Sabnzbd.__new__(Sabnzbd)
        self.downloader.config = {}

    def _mock_conf(self, key):
        config_values = {
            'enabled': 1,
            'host': 'http://localhost:8080/',
            'ssl': 0,
            'api_key': 'test_api_key_123',
            'category': 'movies',
            'priority': 0,
            'delete_failed': True,
            'remove_complete': False,
        }
        return config_values.get(key)

    @mock.patch.object(Sabnzbd, 'conf')
    @mock.patch.object(Sabnzbd, 'urlopen')
    def test_call_constructs_url_with_api_key(self, mock_urlopen, mock_conf):
        mock_conf.side_effect = self._mock_conf
        mock_urlopen.return_value = json.dumps({'version': '4.3.0'}).encode('utf-8')

        result = self.downloader.call({'mode': 'version'})

        self.assertEqual(result, '4.3.0')
        called_url = mock_urlopen.call_args[0][0]
        self.assertIn('apikey=test_api_key_123', called_url)
        self.assertIn('output=json', called_url)
        self.assertIn('mode=version', called_url)

    @mock.patch.object(Sabnzbd, 'call')
    def test_test_connection_successful(self, mock_call):
        mock_call.side_effect = lambda params, **kwargs: (
            '4.3.0' if params['mode'] == 'version' else {'slots': []}
        )

        success = self.downloader.test()
        self.assertTrue(success)

    @mock.patch.object(Sabnzbd, 'call')
    def test_test_connection_rejects_old_version(self, mock_call):
        mock_call.side_effect = lambda params, **kwargs: (
            '0.6.5' if params['mode'] == 'version' else {}
        )

        success, message = self.downloader.test()
        self.assertFalse(success)
        self.assertIn('too old', message)

    @mock.patch.object(Sabnzbd, 'conf')
    @mock.patch.object(Sabnzbd, 'call')
    def test_download_via_url(self, mock_call, mock_conf):
        mock_conf.side_effect = self._mock_conf
        mock_call.return_value = {'status': True, 'nzo_ids': ['SABnzbd_nzo_abc123']}

        data = {
            'name': 'The.Movie.2024.1080p',
            'url': 'https://nzbprovider.example/get?id=123',
        }
        media = {
            'title': 'The Movie',
            'info': {'year': 2024},
        }

        result = self.downloader.download(data=data, media=media)
        self.assertTrue(result)
        called_params = mock_call.call_args[0][0]
        self.assertEqual(called_params['mode'], 'addurl')
        self.assertEqual(called_params['name'], 'https://nzbprovider.example/get?id=123')
        self.assertEqual(called_params['cat'], 'movies')

    @mock.patch.object(Sabnzbd, 'conf')
    @mock.patch.object(Sabnzbd, 'call')
    def test_download_via_filedata(self, mock_call, mock_conf):
        mock_conf.side_effect = self._mock_conf
        mock_call.return_value = {'status': True, 'nzo_ids': ['SABnzbd_nzo_file456']}

        data = {'name': 'The.Movie.2024.1080p'}
        media = {'title': 'The Movie', 'info': {'year': 2024}}
        filedata = b'<?xml version="1.0" encoding="utf-8" ?><nzb>test nzb data content here over 50 bytes</nzb>'

        result = self.downloader.download(data=data, media=media, filedata=filedata)
        self.assertEqual(result, {'id': 'SABnzbd_nzo_file456', 'downloader': 'Sabnzbd', 'status_support': True})
        kwargs = mock_call.call_args[1]
        self.assertIn('files', kwargs)
        filename, content = kwargs['files']['nzbfile']
        self.assertTrue(filename.endswith('.nzb'))
        self.assertEqual(content, filedata)

    @mock.patch.object(Sabnzbd, 'conf')
    @mock.patch.object(Sabnzbd, 'call')
    def test_download_via_filedata_detects_rar(self, mock_call, mock_conf):
        mock_conf.side_effect = self._mock_conf
        mock_call.return_value = {'status': True, 'nzo_ids': ['SABnzbd_nzo_rar789']}

        data = {'name': 'The.Movie.2024.1080p', 'protocol': 'nzb'}
        media = {'title': 'The Movie', 'info': {'year': 2024}}
        filedata = b'Rar!\x1a\x07\x00' + b'A' * 60

        result = self.downloader.download(data=data, media=media, filedata=filedata)
        self.assertEqual(result, {'id': 'SABnzbd_nzo_rar789', 'downloader': 'Sabnzbd', 'status_support': True})
        filename, _ = mock_call.call_args[1]['files']['nzbfile']
        self.assertTrue(filename.endswith('.rar'))

    @mock.patch.object(Sabnzbd, 'call')
    def test_get_all_download_status(self, mock_call):
        mock_call.side_effect = lambda params, **kwargs: (
            {'slots': [{'nzo_id': 'nzo_active_1', 'filename': 'Movie1.nzb', 'status': 'Downloading', 'timeleft': '0:10:00'}], 'paused': False}
            if params['mode'] == 'queue' else
            {'slots': [{'nzo_id': 'nzo_done_2', 'name': 'Movie2', 'status': 'Completed', 'fail_message': '', 'storage': '/downloads/Movie2'}]}
        )

        downloads = self.downloader.getAllDownloadStatus(ids=['nzo_active_1', 'nzo_done_2'])
        self.assertEqual(len(downloads), 2)
        statuses = {d['id']: d['status'] for d in downloads}
        self.assertEqual(statuses['nzo_active_1'], 'busy')
        self.assertEqual(statuses['nzo_done_2'], 'completed')
