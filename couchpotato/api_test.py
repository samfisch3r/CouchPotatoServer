import sys
import unittest
from pathlib import Path

repository_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repository_root))
sys.path.append(str(repository_root / 'libs'))

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from couchpotato.api import (
    ApiHandler,
    NonBlockHandler,
    addApiView,
    api,
    api_locks,
    api_nonblock,
)


class ApiHandlerTest(AsyncHTTPTestCase):

    def setUp(self):
        self.original_api = dict(api)
        self.original_api_locks = dict(api_locks)
        self.original_api_nonblock = dict(api_nonblock)
        super().setUp()

    def tearDown(self):
        try:
            super().tearDown()
        finally:
            api.clear()
            api.update(self.original_api)
            api_locks.clear()
            api_locks.update(self.original_api_locks)
            api_nonblock.clear()
            api_nonblock.update(self.original_api_nonblock)

    def get_app(self):
        api.clear()
        api_locks.clear()
        api_nonblock.clear()
        addApiView('test', lambda **kwargs: {'success': True})
        api_nonblock['listener'] = (
            lambda callback, **kwargs: callback({'ready': True}),
            lambda callback: None,
        )
        return Application([
            (r'/api/(.*)', ApiHandler),
            (r'/nonblock/(.*)', NonBlockHandler),
        ])

    def test_blocking_api_response(self):
        response = self.fetch('/api/test')

        self.assertEqual(response.code, 200)
        self.assertIn(b'"success": true', response.body)

    def test_nonblocking_api_response(self):
        response = self.fetch('/nonblock/listener')

        self.assertEqual(response.code, 200)
        self.assertIn(b'"ready": true', response.body)


class RoutePrecedenceTest(AsyncHTTPTestCase):

    def get_app(self):
        from tornado.web import StaticFileHandler
        from couchpotato import WebHandler, addView
        import os

        static_dir = os.path.join(str(repository_root), 'couchpotato', 'static', 'scripts')
        addView('testview', lambda handler: 'test-view-content')

        app = Application()
        # Static registered first
        app.add_handlers(".*$", [
            (r'/static/scripts/(.*)', StaticFileHandler, {'path': static_dir}),
        ])
        # WebHandler registered last
        app.add_handlers(".*$", [
            (r'/(.*)', WebHandler),
        ])
        return app

    def test_static_file_not_intercepted_by_webhandler(self):
        response = self.fetch('/static/scripts/combined.vendor.min.js')
        self.assertEqual(response.code, 200)
        # Verify it served actual JS file and not HTML / redirect
        self.assertTrue(len(response.body) > 1000)

    def test_webhandler_serves_registered_views(self):
        response = self.fetch('/testview')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, b'test-view-content')


if __name__ == '__main__':
    unittest.main()

