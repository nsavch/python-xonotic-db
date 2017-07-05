import os
import re
import urllib.parse
import time
import logging

from xon_serverdb.crc import crc_block

KEYPAIR_RE = re.compile(r'\\([^\\"]+)\\([^\\"]+)')
DB_BUCKETS = 8192


logger = logging.getLogger(__name__)


def default_hashfunc(inp):
    return crc_block(inp)


class ServerDBException(Exception):
    pass


class ServerDB:
    def __init__(self, data, db_buckets=DB_BUCKETS, hashfunc=default_hashfunc):
        self.db_buckets = db_buckets
        self.hashfunc = hashfunc
        self.contents = {}
        for i in data.splitlines()[1:]:
            self.parse_line(i)

    def parse_line(self, line):
        for i in KEYPAIR_RE.finditer(line):
            key = i.group(1)
            value = urllib.parse.unquote(i.group(2))
            self.contents[key] = value

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
            raise ServerDBException('%s exists and is not a file. Cannot write to it.', file_path)
        lines = [''] * self.db_buckets
        for key, value in self.contents.items():
            lines[self.hashfunc(key) % self.db_buckets] += r'\%s\%s' % (key, urllib.parse.quote(value))
        with open(file_path, 'w') as f:
            f.write('%d\n' % self.db_buckets)
            for i in lines:
                f.write(i + '\n')
