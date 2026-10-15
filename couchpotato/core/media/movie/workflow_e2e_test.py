import os
import shutil
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from CodernityDB.database_super_thread_safe import SuperThreadSafeDatabase
from couchpotato.core.database import Database
from couchpotato.core.downloaders.sabnzbd import Sabnzbd
from couchpotato.core.event import addEvent, fireEvent, events
from couchpotato.core.media._base.media.main import MediaPlugin
from couchpotato.core.media.movie._base.main import MovieBase
from couchpotato.core.media.movie.searcher import MovieSearcher
from couchpotato.core.plugins.profile.main import ProfilePlugin
from couchpotato.core.plugins.quality.main import QualityPlugin
from couchpotato.core.plugins.release.index import ReleaseIndex, ReleaseStatusIndex, ReleaseIDIndex, ReleaseDownloadIndex
from couchpotato.core.plugins.release.main import Release
from couchpotato.environment import Env


class MovieWorkflowEndToEndTest(unittest.TestCase):

    def setUp(self):
        # Clean event registry
        events.clear()

        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'database')
        os.makedirs(self.db_path, exist_ok = True)

        self.db = SuperThreadSafeDatabase(self.db_path)
        self.db.create()

        Env.set('db', self.db)
        Env.set('data_dir', self.temp_dir)
        Env.set('app_dir', os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

        # Initialize core components
        self.database_plugin = Database()
        self.media_plugin = MediaPlugin()
        self.profile_plugin = ProfilePlugin()
        self.quality_plugin = QualityPlugin()
        self.release_plugin = Release()
        self.movie_plugin = MovieBase()
        self.movie_searcher = MovieSearcher()
        self.sabnzbd_plugin = Sabnzbd()

        # Fire database setup to configure all registered plugin indexes
        fireEvent('database.setup')
        fireEvent('quality.fill')

        # Insert a default profile
        self.default_profile = self.db.insert({
            '_t': 'profile',
            'label': 'HD Default',
            'order': 0,
            'core': True,
            'qualities': ['1080p', '720p'],
            'finish': [True, False],
            'wait_for': [0, 0],
            '3d': [False, False],
            'minimum_score': 0,
        })
        self.db.insert({
            '_t': 'profile',
            'label': 'Default',
            'order': 99,
            'core': False,
            'qualities': ['1080p'],
            'finish': [True],
            'wait_for': [0],
            '3d': [False],
            'minimum_score': 0,
        })

    def tearDown(self):
        if self.db.opened:
            self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors = True)
        events.clear()

    def test_complete_movie_workflow_nzb_to_sabnzbd(self):
        # 1. Add Movie to wanted list
        movie_dict = fireEvent('movie.add', params = {
            'identifier': 'tt1375666',
            'title': 'Inception',
            'profile_id': self.default_profile['_id'],
            'info': {
                'year': 2010,
                'titles': ['Inception'],
                'release_dates': {'theater': time.time() - 31536000, 'dvd': time.time() - 30000000},
            }
        }, search_after = False, update_after = False, single = True)

        self.assertIsNotNone(movie_dict)
        self.assertEqual(movie_dict['status'], 'active')
        self.assertEqual(movie_dict['title'], 'Inception')
        self.assertEqual(movie_dict['identifiers']['imdb'], 'tt1375666')

        # 2. Verify media can be retrieved via with_status and get
        active_medias = list(fireEvent('media.with_status', 'active', types = 'movie', single = True))
        self.assertEqual(len(active_medias), 1)
        self.assertEqual(active_medias[0]['_id'], movie_dict['_id'])

        fetched = fireEvent('media.get', movie_dict['_id'], single = True)
        self.assertEqual(fetched['_id'], movie_dict['_id'])

        # 3. Simulate NZB Searcher finding a release from Newznab
        fake_nzb_content = b'<?xml version="1.0" encoding="utf-8" ?>\n<nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">\n<head></head>\n<file></file>\n</nzb>'
        mock_search_results = [{
            'id': 'nzb_12345',
            'name': 'Inception.2010.1080p.BluRay.x264',
            'url': 'https://api.newznab.local/api?t=get&id=nzb_12345&apikey=mockkey',
            'protocol': 'nzb',
            'type': 'movie',
            'size': 4500,  # 4500 MB
            'score': 100,
            'status': 'available',
            'age': 10,
            'provider': 'mock_newznab',
            'download': MagicMock(return_value = fake_nzb_content),
        }]

        # Mock searcher.protocols to include 'nzb'
        addEvent('searcher.protocols', lambda: ['nzb'])
        # Mock searcher.search to return mock_search_results
        addEvent('searcher.search', lambda *args, **kwargs: mock_search_results)
        # Mock searcher.correct_words to accept the release
        addEvent('searcher.correct_words', lambda *args, **kwargs: True)

        # 4. Configure SABnzbd downloader
        with patch.object(self.sabnzbd_plugin, 'conf', side_effect = lambda key, **kw: {
            'enabled': True,
            'api_key': 'sab_secret_key_123',
            'host': 'localhost:8080',
            'category': 'movies',
            'delete_failed': True,
            'manual': False,
        }.get(key, '')):

            # Mock SABnzbd network call to return success response
            with patch.object(self.sabnzbd_plugin, 'urlopen', return_value = '{"status": true, "nzo_ids": ["SABnzbd_nzo_abc123"]}'):
                # 5. Execute searcher.single for the movie
                download_triggered = self.movie_searcher.single(movie_dict, ['nzb'], manual = True, force_download = True)
                self.assertTrue(download_triggered)

        # 6. Verify release was created, downloaded, and recorded in database
        releases = list(fireEvent('release.for_media', movie_dict['_id'], single = True) or [])
        self.assertGreater(len(releases), 0)
        downloaded_release = releases[0]
        self.assertEqual(downloaded_release['status'], 'done')
        self.assertIn('download_info', downloaded_release)
        self.assertEqual(downloaded_release['download_info']['id'], 'SABnzbd_nzo_abc123')
        self.assertEqual(downloaded_release['download_info']['downloader'], 'Sabnzbd')

        # 7. Verify movie media status transitioned to done
        final_movie = fireEvent('media.get', movie_dict['_id'], single = True)
        self.assertEqual(final_movie['status'], 'done')
