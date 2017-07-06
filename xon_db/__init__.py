import os
import re
import urllib.parse
import time
import logging
from collections import UserDict

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
        for i in data.splitlines()[1:]:
            self.parse_line(i)
        super().__init__()

    def parse_line(self, line):
        for i in KEYPAIR_RE.finditer(line):
            key = i.group(1)
            value = urllib.parse.unquote(i.group(2))
            self.data[key] = value

    @classmethod
    def load(cls, file):
        return cls(file.read())

    @staticmethod
    def get_backup_file_name(file_path):
        return file_path + '.%s' % time.time()

    def save(self, file_path):
        if os.path.isfile(file_path):
            with open(self.get_backup_file_name(file_path), 'w') as d:
                with open(file_path, 'r') as o:
                    d.write(o.read())
        elif os.path.exists(file_path):
            raise XonoticDBException('%s exists and is not a file. Cannot write to it.', file_path)
        lines = [''] * self.db_buckets
        for key, value in self.data.items():
            lines[self.hashfunc(key) % self.db_buckets] += r'\%s\%s' % (key, urllib.parse.quote(value))
        with open(file_path, 'w') as f:
            f.write('%d\n' % self.db_buckets)
            for i in lines:
                f.write(i + '\n')
