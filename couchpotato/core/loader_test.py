import sys
import unittest
from pathlib import Path

repository_root = Path(__file__).resolve().parents[2]
sys.path.extend([
    str(repository_root),
    str(repository_root / 'libs'),
    str(repository_root / 'libs' / 'CodernityDB'),
])

from couchpotato.core.loader import Loader


class LoaderDiscoveryTest(unittest.TestCase):

    def setUp(self):
        self.loader = Loader()
        self.loader.preload(root = str(repository_root))

    def test_downloader_discovery_only_includes_sabnzbd(self):
        # Priority 20 contains downloaders
        downloader_modules = {
            name for name in self.loader.modules.get(20, {})
            if name.startswith('couchpotato.core.downloaders')
        }
        self.assertEqual(
            downloader_modules,
            {
                'couchpotato.core.downloaders',
                'couchpotato.core.downloaders.__init__',
                'couchpotato.core.downloaders.sabnzbd',
            }
        )

    def test_nzb_provider_discovery_only_includes_newznab(self):
        # Media provider priority is 25
        nzb_modules = {
            name for name in self.loader.modules.get(25, {})
            if 'providers.nzb' in name
        }
        # Only base and newznab should be discovered
        for mod in nzb_modules:
            self.assertNotIn('binsearch', mod)
            self.assertNotIn('nzbclub', mod)
            self.assertNotIn('omgwtfnzbs', mod)

        has_newznab = any('newznab' in mod for mod in nzb_modules)
        self.assertTrue(has_newznab)

    def test_obsolete_metadata_providers_not_present(self):
        metadata_modules = {
            name for name in self.loader.modules.get(25, {})
            if 'providers.metadata' in name
        }
        for mod in metadata_modules:
            self.assertNotIn('ps3', mod)
            self.assertNotIn('wdtv', mod)
            self.assertNotIn('wmc', mod)
            self.assertNotIn('mediabrowser', mod)

    def test_torrent_providers_not_present(self):
        torrent_modules = {
            name for name in self.loader.modules.get(25, {})
            if 'providers.torrent' in name
        }
        self.assertEqual(len(torrent_modules), 0)

    def test_loader_run_loads_all_modules_without_unhandled_exceptions(self):
        # loader.run() should successfully iterate and load all modules
        self.loader.run()
        total_modules = sum(len(mods) for mods in self.loader.modules.values())
        self.assertGreater(total_modules, 0)
