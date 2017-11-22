import os
import re
import urllib.parse
import time
import logging
from collections import UserDict, defaultdict
from fnmatch import fnmatch

from xon_db.crc import crc_block

KEYPAIR_RE = re.compile(r'\\([^\\"]+)\\([^\\"]+)')
DB_BUCKETS = 8192

logger = logging.getLogger(__name__)


class XonoticDBException(Exception):
    """
    Something went wrong with Xonotic DB
    """
    pass


class XonoticDB(UserDict):
    """
    A class for reading and writing xonotic databases. Provides dict-like interface
    """
    def __init__(self, data: str, db_buckets=DB_BUCKETS, hashfunc=crc_block):
        """
        :param data: database contents
        :param db_buckets: number of buckets (for writing)
        :param hashfunc: default hashfunc. Change with care
        """
        self.db_buckets = db_buckets
        self.hashfunc = hashfunc
        super().__init__()
        for i in data.splitlines()[1:]:
            self.parse_line(i)

    def parse_line(self, line: str):
        """
        Parse a line from database
        :param line: line to parse
        """
        for i in KEYPAIR_RE.finditer(line):
            key = i.group(1)
            value = urllib.parse.unquote(i.group(2))
            self[key] = value

    @classmethod
    def load(cls, file):
        """
        Load a database from an open file
        :param file: file
        :return: XonoticDB instance
        """
        return cls(file.read())

    @classmethod
    def load_path(cls, file_path):
        """
        Load a database from the specified file path
        :param file_path: file path
        :return: XonoticDB instance
        """
        with open(file_path, 'r') as f:
            return cls.load(f)

    @staticmethod
    def get_backup_file_name(file_path):
        """
        Get a file name for backup file
        :param file_path: file path
        :return: backup file name
        """
        return file_path + '.%s.bak' % time.time()

    def save(self, file_path):
        """
        Write database to a file. If a file with the specified name exists it's backed up
        :param file_path: file path
        """
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
        """
        Filter database key by pattern
        :param key_pattern: pattern (either glob or regex)
        :param is_regex: should be True if the pattern is regex
        :return: iterator of (key, value) pairs
        """
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
        """
        Remove a CTS record
        :param map:
        :param position:
        :return:
        """
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

    def remove_all_cts_records_by(self, crypto_idfp):
        """
        Remove all CTS records from the specified player
        :param crypto_idfp:
        :return:
        """
        regex = re.compile('(.+)/cts100record/crypto_idfp(\d+)')
        to_remove = []
        for k, v in self.filter(regex, is_regex=True):
            if v == crypto_idfp:
                match = regex.match(k)
                to_remove.append((match.group(1), int(match.group(2))))
        for i in to_remove:
            self.remove_cts_record(*i)

    def __merge_cts_speeds(self, crypto_idfp, crypto_idfp_list):
        speed_id_regex = re.compile('(.+)/cts100record/speed/crypto_idfp')
        speed_value_regex = re.compile('(.+)/cts100record/speed/speed')
        speeds = defaultdict(dict)  # map -> idfp -> speed
        for k, v in self.filter(speed_id_regex, is_regex=True):
            if v in crypto_idfp_list:
                self[k] = crypto_idfp

    def __merge_cts_times(self, crypto_idfp, crypto_idfp_list):
        time_id_regex = re.compile('(.+)/cts100record/crypto_idfp(\d+)')
        target_records = {}  # map -> position
        for k, idfp in self.filter(time_id_regex, is_regex=True):
            if idfp == crypto_idfp:
                match = time_id_regex.match(k)
                position = int(match.group(2))
                target_records[match.group(1)] = position
        candidate_records = defaultdict(list)  # map -> [position]
        for k, idfp in self.filter(time_id_regex, is_regex=True):
            if idfp in crypto_idfp_list:
                match = time_id_regex.match(k)
                position = int(match.group(2))
                candidate_records[match.group(1)].append(position)
        for map_, results in candidate_records.items():
            results.sort()
            if map_ not in target_records or results[0] < target_records[map_]:
                # either target not set a record on this map, or set a worse record than one of candidates
                self['{}/cts100record/crypto_idfp{}'.format(map_, results[0])] = crypto_idfp
                for i in results[1:]:
                    self.remove_cts_record(map_, i)
                if map_ in target_records:
                    self.remove_cts_record(map_, target_records[map_])
            else:
                # all candidates worse than the target
                for i in results:
                    self.remove_cts_record(map_, i)

    def merge_cts_records(self, crypto_idfp, crypto_idfp_list):
        """
        Merge all CTS records (including speed) of each player in crypto_idfp_list with records of crypto_idfp
        :param crypto_idfp: Target player, who will now own all records of players in crypto_idfp_list
        :param crypto_idfp_list: List of crypto_idfp
        :return:
        """
        self.__merge_cts_times(crypto_idfp, crypto_idfp_list)
        self.__merge_cts_speeds(crypto_idfp, crypto_idfp_list)
        for i in crypto_idfp_list:
            del self['/uid2name/{}'.format(i)]
