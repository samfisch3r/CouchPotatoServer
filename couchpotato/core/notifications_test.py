import sys
import unittest
from pathlib import Path
from unittest.mock import patch

repository_root = Path(__file__).resolve().parents[2]
sys.path.extend([
    str(repository_root),
    str(repository_root / 'libs'),
    str(repository_root / 'libs' / 'CodernityDB'),
])

from couchpotato.core.loader import Loader
from couchpotato.core.notifications import core as core_notifications
from couchpotato.core.notifications.core import main as core_main
from couchpotato.core.plugins import base as plugin_base


class NotificationConfigurationRemovalTest(unittest.TestCase):

    def test_loader_discovers_only_in_app_notification_center(self):
        loader = Loader()
        notifications_path = (
            repository_root / 'couchpotato' / 'core' / 'notifications')

        loader.addFromDir(
            'notifications',
            20,
            'couchpotato.core.notifications',
            str(notifications_path),
        )

        self.assertEqual(
            set(loader.modules[20]),
            {
                'couchpotato.core.notifications',
                'couchpotato.core.notifications.__init__',
                'couchpotato.core.notifications.core',
            },
        )
        self.assertFalse(hasattr(core_notifications, 'config'))

    def test_core_notifier_keeps_frontend_event_listeners(self):
        with (
            patch.object(plugin_base, 'addEvent'),
            patch.object(core_main, 'addEvent') as add_event,
            patch.object(core_main, 'fireEvent'),
            patch.object(core_main, 'addApiView'),
            patch.object(core_main, 'addNonBlockApiView'),
        ):
            notifier = core_main.CoreNotifier()

        event_handlers = {
            call.args[0]: call.args[1]
            for call in add_event.call_args_list
        }
        events = set(event_handlers)
        self.assertIn('notify.frontend', events)
        self.assertIn('media.available', events)
        self.assertIn('movie.snatched', events)
        self.assertIn('core.message.important', events)

        with patch.object(notifier, 'notify') as notify:
            event_handlers['media.available'](
                'message',
                {'group': 'group data'},
                {'data': 'event data'},
            )

        notify.assert_called_once_with(
            message='message',
            data={'data': 'event data'},
            listener='media.available',
        )


if __name__ == '__main__':
    unittest.main()
