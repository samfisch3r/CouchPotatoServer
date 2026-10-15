import time
import unittest
from datetime import date
from unittest import mock

from couchpotato.core.media.movie.searcher import MovieSearcher


class MovieSearcherTest(unittest.TestCase):

    def setUp(self):
        self.searcher = MovieSearcher.__new__(MovieSearcher)
        self.searcher.in_progress = False

    def test_could_be_released_handles_none_and_empty_dates(self):
        current_year = date.today().year

        # None dates
        self.assertTrue(self.searcher.couldBeReleased(False, None, current_year))
        # Empty dates
        self.assertTrue(self.searcher.couldBeReleased(False, {}, current_year))
        # Dict with None values for theater and dvd
        self.assertFalse(self.searcher.couldBeReleased(False, {'theater': None, 'dvd': None}, current_year))

    def test_could_be_released_before_1972_or_negative_dates(self):
        current_year = date.today().year
        self.assertTrue(self.searcher.couldBeReleased(False, {'theater': -1}, current_year))
        self.assertTrue(self.searcher.couldBeReleased(False, {'dvd': -1}, current_year))

    def test_could_be_released_future_year(self):
        now_year = date.today().year
        # Year far in future is not released
        self.assertFalse(self.searcher.couldBeReleased(False, {'theater': 0, 'dvd': 0}, now_year + 5))

    def test_could_be_released_dvd_date(self):
        now = time.time()
        current_year = date.today().year

        # DVD released 1 day ago
        self.assertTrue(self.searcher.couldBeReleased(False, {'theater': 0, 'dvd': now - 86400}, current_year))
        # DVD releases in 3 days (within 4 weeks before dvd)
        self.assertTrue(self.searcher.couldBeReleased(False, {'theater': 0, 'dvd': now + (3 * 86400)}, current_year))
        # DVD releases in 6 months (beyond 4 weeks)
        self.assertFalse(self.searcher.couldBeReleased(False, {'theater': 0, 'dvd': now + (180 * 86400)}, current_year))

    def test_could_be_released_theater_date(self):
        now = time.time()
        current_year = date.today().year

        # Theater release 14 weeks ago (beyond 12 weeks = 7257600s)
        self.assertTrue(self.searcher.couldBeReleased(False, {'theater': now - (14 * 7 * 86400), 'dvd': 0}, current_year))
        # Theater release 2 weeks ago (not yet 12 weeks)
        self.assertFalse(self.searcher.couldBeReleased(False, {'theater': now - (2 * 7 * 86400), 'dvd': 0}, current_year))

    def test_could_be_released_prerelease(self):
        now = time.time()
        current_year = date.today().year

        # Prerelease 3 days before theater (within 1 week = 604800s)
        self.assertTrue(self.searcher.couldBeReleased(True, {'theater': now + (3 * 86400), 'dvd': 0}, current_year))
        # Prerelease 3 weeks before theater (too early)
        self.assertFalse(self.searcher.couldBeReleased(True, {'theater': now + (21 * 86400), 'dvd': 0}, current_year))

    def test_get_progress(self):
        self.searcher.in_progress = {'total': 10, 'to_go': 3}
        with mock.patch.object(self.searcher, 'getType', return_value='movie'):
            progress = self.searcher.getProgress()
        self.assertEqual(progress, {'movie': {'total': 10, 'to_go': 3}})
