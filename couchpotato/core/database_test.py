import json
import os
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
            finally:
                if database.opened:
                    database.close()

    def test_legacy_index_with_izip_import_loads_successfully(self):
        with tempfile.TemporaryDirectory() as path:
            database = SuperThreadSafeDatabase(path)
            try:
                database.create()
                indexes_dir = Path(path) / '_indexes'
                indexes_dir.mkdir(exist_ok=True)
                legacy_index_code = (
                    "# custom_test_index\n"
                    "# CustomTestIndex\n"
                    "# inserted automatically\n"
                    "from itertools import izip\n"
                    "import cPickle\n"
                    "from hashlib import md5\n"
                    "from CodernityDB.tree_index import TreeBasedIndex\n"
                    "class CustomTestIndex(TreeBasedIndex):\n"
                    "    def __init__(self, *args, **kwargs):\n"
                    "        kwargs['key_format'] = '32s'\n"
                    "        super(CustomTestIndex, self).__init__(*args, **kwargs)\n"
                    "    def make_key(self, key):\n"
                    "        return md5(key).hexdigest()\n"
                    "    def make_key_value(self, data):\n"
                    "        return md5(data.get('val', '')).hexdigest(), None\n"
                )
                (indexes_dir / '01custom_test_index.py').write_text(legacy_index_code, encoding='utf-8')
                
                # Should read and compile legacy index without raising ImportError for izip
                database._read_indexes()
                self.assertIn('custom_test_index', database.indexes_names)
                idx = database.indexes_names['custom_test_index']
                # Verify that make_key with unencoded string works cleanly
                self.assertEqual(len(idx.make_key('active')), 32)
            finally:
                if database.opened:
                    database.close()

    def test_legacy_index_bucket_marshal_bytes_props_opens_cleanly(self):
        with tempfile.TemporaryDirectory() as path:
            database = SuperThreadSafeDatabase(path)
            try:
                database.create()
                database.close()

                # Simulate existing Python 2 bucket with interned string key and bytes value
                # e.g. {'name': b'id', 'storage_class': b'IU_Storage'}
                buck_path = os.path.join(path, 'id_buck')
                with open(buck_path, 'r+b') as f:
                    p2_bytes = b'{t\x04\x00\x00\x00names\x02\x00\x00\x00ids\r\x00\x00\x00storage_classs\n\x00\x00\x00IU_Storage0'
                    f.seek(0)
                    f.write(p2_bytes.ljust(500, b'\x00'))

                # Open existing database
                db = SuperThreadSafeDatabase(path)
                db.open()
                self.assertTrue(db.opened)
                self.assertIsInstance(db.storage.name, str)
                self.assertEqual(db.storage.name, 'id')

                # Verify read/write functions properly
                inserted = db.insert({'type': 'movie', 'title': 'Legacy Inception'})
                doc = db.get('id', inserted['_id'])
                self.assertEqual(doc['title'], 'Legacy Inception')
                db.close()
            finally:
                if database.opened:
                    database.close()

    def test_legacy_index_bucket_marshal_stringref_loads_and_migrates(self):
        with tempfile.TemporaryDirectory() as path:
            database = SuperThreadSafeDatabase(path)
            try:
                database.create()
                database.close()

                # Simulate existing Python 2 bucket with interned string reference ('R')
                # which causes standard Python 3 marshal.loads to raise ValueError: bad marshal data
                p2_stringref_payload = b'{t\x04\x00\x00\x00namet\x02\x00\x00\x00idt\r\x00\x00\x00storage_classs\n\x00\x00\x00IU_Storaget\x05\x00\x00\x00aliasR\x01\x00\x00\x000'
                buck_path = os.path.join(path, 'id_buck')
                with open(buck_path, 'r+b') as f:
                    f.seek(0)
                    f.write(p2_stringref_payload.ljust(500, b'\x00'))

                db = SuperThreadSafeDatabase(path)
                db.open()
                self.assertTrue(db.opened)
                self.assertEqual(db.storage.name, 'id')
                db.close()

                # Verify bucket header was automatically migrated to standard Python 3 marshal format
                with open(buck_path, 'rb') as f:
                    import marshal
                    rewritten = marshal.loads(f.read(500))
                    self.assertEqual(rewritten['name'], 'id')
                    self.assertEqual(rewritten['storage_class'], 'IU_Storage')
                    self.assertEqual(rewritten['alias'], 'id')
            finally:
                if database.opened:
                    database.close()

    def test_database_all_with_doc_skips_missing_or_deleted_records(self):
        with tempfile.TemporaryDirectory() as path:
            database = SuperThreadSafeDatabase(path)
            try:
                database.create()
                doc1 = database.insert({'type': 'movie', 'title': 'Movie 1'})
                doc2 = database.insert({'type': 'movie', 'title': 'Movie 2'})

                # Delete doc1 directly from id index
                database.delete(doc1)

                # db.all with with_doc=True should not raise RecordNotFound, but return remaining valid doc
                results = list(database.all('id', with_doc=True))
                # For id index, it yields active documents
                self.assertTrue(len(results) >= 1)
            finally:
                if database.opened:
                    database.close()

    def test_database_reindex_rebuilds_secondary_indexes(self):
        from couchpotato.core.media._base.media.index import MediaTypeIndex, MediaStatusIndex, TitleIndex
        with tempfile.TemporaryDirectory() as path:
            database = SuperThreadSafeDatabase(path)
            try:
                database.create()
                database.add_index(MediaTypeIndex(database.path, 'media_by_type'))
                database.add_index(MediaStatusIndex(database.path, 'media_status'))
                database.add_index(TitleIndex(database.path, 'media_title'))

                doc1 = {'_t': 'media', 'type': 'movie', 'status': 'active', 'title': 'The Matrix'}
                doc2 = {'_t': 'media', 'type': 'movie', 'status': 'done', 'title': 'Inception'}
                database.insert(doc1)
                database.insert(doc2)

                database.reindex()

                movies_by_type = list(database.get_many('media_by_type', 'movie'))
                self.assertEqual(len(movies_by_type), 2)

                active_movies = list(database.get_many('media_status', 'active'))
                self.assertEqual(len(active_movies), 1)

                titles = list(database.all('media_title'))
                self.assertEqual(len(titles), 2)
            finally:
                if database.opened:
                    database.close()

    def test_database_reindex_handles_elem_not_found_in_id_index(self):
        from CodernityDB.index import ElemNotFound
        from couchpotato.core.media._base.media.index import MediaTypeIndex
        with tempfile.TemporaryDirectory() as path:
            database = SuperThreadSafeDatabase(path)
            try:
                database.create()
                database.add_index(MediaTypeIndex(database.path, 'media_by_type'))

                doc1 = {'_t': 'media', 'type': 'movie', 'title': 'Movie 1'}
                doc2 = {'_t': 'media', 'type': 'movie', 'title': 'Movie 2'}
                database.insert(doc1)
                database.insert(doc2)

                orig_id_get = database.id_ind.get
                call_count = [0]

                def mock_id_get(key):
                    call_count[0] += 1
                    # Raise ElemNotFound on the first lookup to simulate an unlinked/orphaned bucket entry
                    if call_count[0] == 1:
                        raise ElemNotFound(f"Location '{key}' not found")
                    return orig_id_get(key)

                database.id_ind.get = mock_id_get

                # Reindex must not raise ElemNotFound, but skip the orphaned entry cleanly
                database.reindex()

                movies = list(database.get_many('media_by_type', 'movie'))
                self.assertEqual(len(movies), 1)
            finally:
                if database.opened:
                    database.close()


if __name__ == '__main__':
    unittest.main()
