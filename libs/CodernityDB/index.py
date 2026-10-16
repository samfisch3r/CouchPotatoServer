#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2011-2013 Codernity (http://codernity.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import marshal

import struct
import shutil

from CodernityDB.storage import IU_Storage, DummyStorage

try:
    from CodernityDB import __version__
except ImportError:
    from __init__ import __version__


import io


class IndexException(Exception):
    pass


class IndexNotFoundException(IndexException):
    pass


class ReindexException(IndexException):
    pass


class TryReindexException(ReindexException):
    pass


class ElemNotFound(IndexException):
    pass


class DocIdNotFound(ElemNotFound):
    pass


class IndexConflict(IndexException):
    pass


class IndexPreconditionsException(IndexException):
    pass


def py2_marshal_loads(b):
    pos = 0
    interned = []

    def read_obj():
        nonlocal pos
        if pos >= len(b):
            raise EOFError('EOF in py2_marshal')
        type_code = b[pos:pos+1]
        pos += 1
        if type_code == b'N':
            return None
        elif type_code == b'T':
            return True
        elif type_code == b'F':
            return False
        elif type_code == b'i':
            val = struct.unpack('<i', b[pos:pos+4])[0]
            pos += 4
            return val
        elif type_code == b'I':
            val = struct.unpack('<q', b[pos:pos+8])[0]
            pos += 8
            return val
        elif type_code == b'g':
            val = struct.unpack('<d', b[pos:pos+8])[0]
            pos += 8
            return val
        elif type_code == b'f':
            length = b[pos]
            pos += 1
            val = float(b[pos:pos+length])
            pos += length
            return val
        elif type_code == b's':
            length = struct.unpack('<i', b[pos:pos+4])[0]
            pos += 4
            val = b[pos:pos+length]
            pos += length
            try:
                return val.decode('utf-8', 'surrogateescape')
            except Exception:
                return val
        elif type_code == b't':
            length = struct.unpack('<i', b[pos:pos+4])[0]
            pos += 4
            raw = b[pos:pos+length]
            pos += length
            val = raw.decode('utf-8', 'surrogateescape')
            interned.append(val)
            return val
        elif type_code == b'R':
            idx = struct.unpack('<i', b[pos:pos+4])[0]
            pos += 4
            return interned[idx]
        elif type_code == b'u':
            length = struct.unpack('<i', b[pos:pos+4])[0]
            pos += 4
            val = b[pos:pos+length].decode('utf-8', 'surrogateescape')
            pos += length
            return val
        elif type_code in (b'(', b'['):
            length = struct.unpack('<i', b[pos:pos+4])[0]
            pos += 4
            items = [read_obj() for _ in range(length)]
            return tuple(items) if type_code == b'(' else items
        elif type_code == b'{':
            res = {}
            while True:
                if pos >= len(b) or b[pos:pos+1] == b'0':
                    pos += 1
                    break
                k = read_obj()
                v = read_obj()
                res[k] = v
            return res
        elif type_code == b'0':
            return None
        else:
            raise ValueError(f'Unknown py2 marshal code {type_code!r} at offset {pos-1}')

    return read_obj()


class Index(object):

    __version__ = __version__

    custom_header = ""  # : use it for imports required by your index

    def __init__(self,
                 db_path,
                 name):
        if isinstance(name, bytes):
            name = name.decode('utf-8', 'surrogateescape')
        self.name = name
        self._start_ind = 500
        self.db_path = db_path

    def open_index(self):
        if not os.path.isfile(os.path.join(self.db_path, self.name + '_buck')):
            raise IndexException("Doesn't exists")
        self.buckets = io.open(
            os.path.join(self.db_path, self.name + "_buck"), 'r+b', buffering=0)
        self._fix_params()
        self._open_storage()

    def _close(self):
        if hasattr(self, 'buckets') and self.buckets and not getattr(self.buckets, 'closed', False):
            self.buckets.close()
        if hasattr(self, 'storage') and self.storage and not getattr(self.storage, 'closed', False):
            self.storage.close()

    def close_index(self):
        if hasattr(self, 'buckets') and self.buckets and not getattr(self.buckets, 'closed', False):
            self.flush()
            self.fsync()
        self._close()

    def create_index(self):
        raise NotImplementedError()

    def _fix_params(self):
        self.buckets.seek(0)
        raw_data = self.buckets.read(self._start_ind)
        needs_rewrite = False
        try:
            props = marshal.loads(raw_data)
        except Exception:
            try:
                props = py2_marshal_loads(raw_data)
                needs_rewrite = True
            except Exception:
                props = {}
        if not isinstance(props, dict):
            props = {}

        clean_props = {}
        for k, v in props.items():
            if isinstance(k, bytes):
                k = k.decode('ascii', 'surrogateescape')
            if isinstance(v, bytes):
                v = v.decode('utf-8', 'surrogateescape')
            clean_props[k] = v
            self.__dict__[k] = v

        if needs_rewrite and clean_props:
            try:
                data = marshal.dumps(clean_props)
                if len(data) <= self._start_ind:
                    self.buckets.seek(0)
                    self.buckets.write(data)
                    self.flush()
            except Exception:
                pass

        self.buckets.seek(0, 2)

    def _save_params(self, in_params={}):
        self.buckets.seek(0)
        raw_data = self.buckets.read(self._start_ind)
        try:
            props = marshal.loads(raw_data)
        except Exception:
            try:
                props = py2_marshal_loads(raw_data)
            except Exception:
                props = {}
        if not isinstance(props, dict):
            props = {}

        clean_props = {}
        for k, v in props.items():
            if isinstance(k, bytes):
                k = k.decode('ascii', 'surrogateescape')
            if isinstance(v, bytes):
                v = v.decode('utf-8', 'surrogateescape')
            clean_props[k] = v
        clean_props.update(in_params)
        self.buckets.seek(0)
        data = marshal.dumps(clean_props)
        if len(data) > self._start_ind:
            raise IndexException("To big props")
        self.buckets.write(data)
        self.flush()
        self.buckets.seek(0, 2)
        self.__dict__.update(clean_props)

    def _open_storage(self, *args, **kwargs):
        pass

    def _create_storage(self, *args, **kwargs):
        pass

    def _destroy_storage(self, *args, **kwargs):
        self.storage.destroy()

    def _find_key(self, key):
        raise NotImplementedError()

    def update(self, doc_id, key, start, size):
        raise NotImplementedError()

    def insert(self, doc_id, key, start, size):
        raise NotImplementedError()

    def get(self, key):
        raise NotImplementedError()

    def get_many(self, key, start_from=None, limit=0):
        raise NotImplementedError()

    def all(self, start_pos):
        raise NotImplementedError()

    def delete(self, key, start, size):
        raise NotImplementedError()

    def make_key_value(self, data):
        raise NotImplementedError()

    def make_key(self, data):
        raise NotImplementedError()

    def compact(self, *args, **kwargs):
        raise NotImplementedError()

    def destroy(self, *args, **kwargs):
        self._close()
        bucket_file = os.path.join(self.db_path, self.name + '_buck')
        os.unlink(bucket_file)
        self._destroy_storage()
        self._find_key.clear()

    def flush(self):
        try:
            self.buckets.flush()
            self.storage.flush()
        except:
            pass

    def fsync(self):
        try:
            os.fsync(self.buckets.fileno())
            self.storage.fsync()
        except:
            pass

    def update_with_storage(self, doc_id, key, value):
        if value:
            start, size = self.storage.insert(value)
        else:
            start = 1
            size = 0
        return self.update(doc_id, key, start, size)

    def insert_with_storage(self, doc_id, key, value):
        if value:
            start, size = self.storage.insert(value)
        else:
            start = 1
            size = 0
        return self.insert(doc_id, key, start, size)
