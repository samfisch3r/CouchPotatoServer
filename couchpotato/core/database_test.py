import json
import sys
import tempfile
import unittest
from pathlib import Path

repository_root = Path(__file__).resolve().parents[2]
sys.path.extend([
    str(repository_root),
    str(repository_root / 'libs'),
    str(repository_root / 'libs' / 'CodernityDB'),
])

from CodernityDB.database_super_thread_safe import SuperThreadSafeDatabase
from CodernityDB.hash_index import _python2_string_hash
from CodernityDB.tree_index import TreeBasedIndex, struct as tree_struct
from couchpotato.core.plugins.quality.index import QualityIndex


class TextTreeIndex(TreeBasedIndex):

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        return data


class DatabasePython3Test(unittest.TestCase):

    def test_hash_index_keeps_python2_string_hash_positions(self):
        self.assertEqual(_python2_string_hash(b''), 0)
        self.assertEqual(_python2_string_hash(b'a'), 12416037344)
        self.assertEqual(_python2_string_hash(b'abc'), 1453079729188098211)
        self.assertEqual(_python2_string_hash('abc'), 1453079729188098211)

    def test_tree_struct_keeps_one_byte_string_keys_binary(self):
        self.assertEqual(tree_struct.unpack('<1s', b'd')[0], b'd')

    def test_quality_index_records_round_trip_as_json(self):
        with tempfile.TemporaryDirectory() as path:
            database = SuperThreadSafeDatabase(path)
            try:
                database.create()
                database.add_index(QualityIndex(path, 'quality'))
                database.insert({
                    '_t': 'quality',
                    'identifier': '1080p',
                })

                record = database.get('quality', '1080p', with_doc=True)

                self.assertEqual(record['doc']['identifier'], '1080p')
                self.assertIsInstance(record['_id'], str)
                json.dumps(record)
            finally:
                if database.opened:
                    database.close()

    def test_tree_index_text_keys_survive_splits_and_reopen(self):
        with tempfile.TemporaryDirectory() as path:
            index = TextTreeIndex(path, 'tree')
            try:
                index.create_index()
                entries = [(f'{i:032d}', f'{i:032d}') for i in range(15)]
                for doc_id, key in entries:
                    index.insert(doc_id, key, 0, 0)

                ranged = list(index.get_between(
                    entries[2][1], entries[12][1], limit=20))
                self.assertEqual(len(ranged), 11)
                self.assertEqual(index.get(entries[8][1])[0], entries[8][0].encode())

                index.update(entries[8][0], entries[8][1], 2, 3)
                self.assertEqual(index.get(entries[8][1])[2:4], (2, 3))
                index.delete(entries[8][0], entries[8][1])
                self.assertEqual(len(list(index.all())), 14)
                index.close_index()

                index.open_index()
                self.assertEqual(index.get(entries[9][1])[0], entries[9][0].encode())
            finally:
                if getattr(index, 'buckets', None) and not index.buckets.closed:
                    index.close_index()

    def test_storage_data_from_decodes_python2_byte_keys_and_values(self):
        with tempfile.TemporaryDirectory() as path:
            database = SuperThreadSafeDatabase(path)
            try:
                database.create()
                # Simulate Python 2 dumped document with bytes keys and values
                py2_bytes = b'{s\x05\x00\x00\x00titles\t\x00\x00\x00Inceptions\x04\x00\x00\x00yeari\xda\x07\x00\x00s\n\x00\x00\x00identifiers\t\x00\x00\x00tt13756660'
                decoded = database.storage.data_from(py2_bytes)
                self.assertIsInstance(decoded['title'], str)
                self.assertEqual(decoded['title'], 'Inception')
                self.assertEqual(decoded['year'], 2010)
                self.assertIsInstance(decoded['identifier'], str)
                self.assertEqual(decoded['identifier'], 'tt1375666')
            finally:
                if database.opened:
                    database.close()


if __name__ == '__main__':
    unittest.main()
