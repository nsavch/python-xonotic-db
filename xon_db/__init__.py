import os
import re
import urllib.parse
import time
import logging
from collections import UserDict
from fnmatch import fnmatch

from xon_db.crc import crc_block

KEYPAIR_RE = re.compile(r'\\([^\\"]+)\\([^\\"]+)')
DB_BUCKETS = 8192

logger = logging.getLogger(__name__)


class XonoticDBException(Exception):
    pass


class XonoticDB(UserDict):
    def __init__(self, data, db_buckets=DB_BUCKETS, hashfunc=crc_block):
        self.db_buckets = db_buckets
        self.hashfunc = hashfunc
        super().__init__()
        for i in data.splitlines()[1:]:
            self.parse_line(i)

    def parse_line(self, line):
        for i in KEYPAIR_RE.finditer(line):
            key = i.group(1)
            value = urllib.parse.unquote(i.group(2))
            self[key] = value

    @classmethod
    def load(cls, file):
        return cls(file.read())

    @classmethod
    def load_path(cls, file_path):
        with open(file_path, 'r') as f:
            return cls(f.read())

    @staticmethod
    def get_backup_file_name(file_path):
        return file_path + '.%s.bak' % time.time()

    def save(self, file_path):
        if os.path.isfile(file_path):
            with open(self.get_backup_file_name(file_path), 'w') as d:
                with open(file_path, 'r') as o:
                    d.write(o.read())
        elif os.path.exists(file_path):
            raise XonoticDBException('%s exists and is not a file. Cannot write to it.', file_path)
        lines = [''] * self.db_buckets
        for key, value in self.items():
            lines[self.hashfunc(key) % self.db_buckets] += r'\%s\%s' % (key, urllib.parse.quote(value))
        with open(file_path, 'w') as f:
            f.write('%d\n' % self.db_buckets)
            for i in lines:
                f.write(i + '\n')

    def filter(self, key_pattern='*', is_regex=False):
        if is_regex:
            if isinstance(key_pattern, str):
                regex = re.compile(key_pattern)
            else:
                regex = key_pattern
        else:
            regex = None
        for k, v in self.items():
            if regex and regex.match(k) or (not regex) and fnmatch(k, key_pattern):
                yield k, v

    def remove_cts_record(self, map, position):
        def _key1(pos):
            return '%s/cts100record/crypto_idfp%s' % (map, pos)

        def _key2(pos):
            return '%s/cts100record/time%s' % (map, pos)

        for i in range(position, 100):
            if _key1(i) in self:
                del self[_key1(i)]
            if _key2(i) in self:
                del self[_key2(i)]
            if _key1(i+1) in self:
                self[_key1(i)] = self[_key1(i+1)]
            if _key2(i+1) in self:
                self[_key2(i)] = self[_key2(i+1)]

    def remove_all_records_by(self, crypto_idfp):
        regex = re.compile('(.+)/cts100record/crypto_idfp(\d+)')
        to_remove = []
        for k, v in self.filter(regex, is_regex=True):
            if v == crypto_idfp:
                match = regex.match(k)
                to_remove.append((match.group(1), int(match.group(2))))
        for i in to_remove:
            self.remove_cts_record(*i)
