import time
import unittest
from unittest import mock

from couchpotato.core.plugins.dashboard import Dashboard


class DashboardTest(unittest.TestCase):

    def setUp(self):
        self.dashboard = Dashboard.__new__(Dashboard)

    @mock.patch('couchpotato.core.plugins.dashboard.get_db')
    @mock.patch('couchpotato.core.plugins.dashboard.fireEvent')
    def test_get_soon_view_none_eta_date(self, mock_fireEvent, mock_get_db):
        mock_db = mock.MagicMock()
        mock_get_db.return_value = mock_db

        now = time.time()

        # Profiles
        profiles = [{'_id': 'profile_1', 'qualities': ['1080p']}]
        pre_releases = [] # 1080p is post theater -> dvd

        # Active medias
        active_ids = [{'_id': 'media_1'}]

        movie_doc = {
            '_id': 'media_1',
            'profile_id': 'profile_1',
            'info': {
                'title': 'Test Movie',
                'year': 2024,
                'release_date': {'theater': None, 'dvd': None}
            }
        }
        mock_db.all.return_value = active_ids
        mock_db.get.return_value = movie_doc

        def fake_fireEvent(event, *args, **kwargs):
            if event == 'profile.all':
                return profiles
            elif event == 'quality.pre_releases':
                return pre_releases
            elif event == 'media.with_status':
                return active_ids
            elif event == 'movie.searcher.could_be_released':
                # Returns True (could be released)
                return True
            elif event == 'release.for_media':
                return []
            return None

        mock_fireEvent.side_effect = fake_fireEvent

        # 1. Soon view (late=False): eta is None, so eta_3month_passed=True -> should NOT be in Soon view
        res_soon = self.dashboard.getSoonView(late = False)
        self.assertTrue(res_soon['success'])
        self.assertEqual(len(res_soon['movies']), 0)
        self.assertTrue(res_soon['empty'])

        # 2. Late view (late=True): eta is None, so eta_3month_passed=True -> SHOULD be in Late view
        res_late = self.dashboard.getSoonView(late = True)
        self.assertTrue(res_late['success'])
        self.assertEqual(len(res_late['movies']), 1)
        self.assertFalse(res_late['empty'])

    @mock.patch('couchpotato.core.plugins.dashboard.get_db')
    @mock.patch('couchpotato.core.plugins.dashboard.fireEvent')
    def test_get_soon_view_with_future_date(self, mock_fireEvent, mock_get_db):
        mock_db = mock.MagicMock()
        mock_get_db.return_value = mock_db

        now = time.time()

        profiles = [{'_id': 'profile_1', 'qualities': ['cam']}]
        pre_releases = ['cam'] # theater

        active_ids = [{'_id': 'media_2'}]

        movie_doc = {
            '_id': 'media_2',
            'profile_id': 'profile_1',
            'info': {
                'title': 'Upcoming Movie',
                'year': 2026,
                'release_date': {'theater': now + 86400 * 7, 'dvd': 0}
            }
        }
        mock_db.all.return_value = active_ids
        mock_db.get.return_value = movie_doc

        def fake_fireEvent(event, *args, **kwargs):
            if event == 'profile.all':
                return profiles
            elif event == 'quality.pre_releases':
                return pre_releases
            elif event == 'media.with_status':
                return active_ids
            elif event == 'movie.searcher.could_be_released':
                return True
            elif event == 'release.for_media':
                return []
            return None

        mock_fireEvent.side_effect = fake_fireEvent

        # Soon view should include upcoming movie
        res_soon = self.dashboard.getSoonView(late = False)
        self.assertTrue(res_soon['success'])
        self.assertEqual(len(res_soon['movies']), 1)
        self.assertEqual(res_soon['movies'][0]['_id'], 'media_2')

        # Late view should NOT include upcoming movie
        res_late = self.dashboard.getSoonView(late = True)
        self.assertTrue(res_late['success'])
        self.assertEqual(len(res_late['movies']), 0)


if __name__ == '__main__':
    unittest.main()
