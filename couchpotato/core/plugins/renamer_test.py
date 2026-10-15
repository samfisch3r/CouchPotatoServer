import io
import os
import tempfile
import unittest
from unittest import mock

from couchpotato.core.plugins.renamer import _extractRarFiles


class FakeRarInfo:

    def __init__(self, filename, is_directory=False):
        self.filename = filename
        self._is_directory = is_directory

    def is_dir(self):
        return self._is_directory


class FakeRarFile:

    def __init__(self, members):
        self.members = members

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def infolist(self):
        return [info for info, _ in self.members]

    def open(self, info):
        contents = next(contents for member, contents in self.members if member is info)
        return io.BytesIO(contents)


class RenamerRarExtractionTest(unittest.TestCase):

    def test_extracts_files_flat_and_preserves_existing_files(self):
        members = [
            (FakeRarInfo('folder/movie.mkv'), b'movie contents'),
            (FakeRarInfo('folder\\subtitles.srt'), b'subtitle contents'),
            (FakeRarInfo('folder/'), b''),
        ]
        archive = FakeRarFile(members)

        with tempfile.TemporaryDirectory() as destination:
            existing_file = os.path.join(destination, 'movie.mkv')
            with open(existing_file, 'wb') as output:
                output.write(b'existing contents')

            with mock.patch('couchpotato.core.plugins.renamer.rarfile.RarFile', return_value=archive):
                extracted = _extractRarFiles('archive.rar', destination)

            self.assertEqual(extracted, [os.path.join(destination, 'subtitles.srt')])
            with open(existing_file, 'rb') as source:
                self.assertEqual(source.read(), b'existing contents')
            with open(extracted[0], 'rb') as source:
                self.assertEqual(source.read(), b'subtitle contents')
