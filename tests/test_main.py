import os

import pytest

from xon_db import XonoticDB, XonoticDBException


def test_load():
    db = XonoticDB.load_path('tests/example.db')
    assert len(db) == 3264


def test_backup_file_name():
    db = XonoticDB('')
    f1 = db.get_backup_file_name('example.db')
    f2 = db.get_backup_file_name('example.db')
    assert f1.endswith('.bak') and f2.endswith('.bak')
    assert f1 != f2


def test_filter():
    db = XonoticDB.load_path('tests/example.db')
    for k, v in db.filter('flatland/*'):
        assert k.startswith('flatland/')
    for k, v in db.filter('flat.*land', is_regex=True):
        assert k.startswith('flatland/')


def test_remove_cts_records():
    db = XonoticDB.load_path('tests/example.db')
    assert len(list(db.filter('flatland/*'))) == 27
    crypto_idfp = db['flatland/cts100record/crypto_idfp5']
    time = db['flatland/cts100record/time5']
    db.remove_all_cts_records_by('1FcXJuGP7Sl4Oxh4ZkN0qf+ZGZEMmocI6GltiENp64g=')
    assert len(list(db.filter('flatland/*'))) == 25
    assert db['flatland/cts100record/crypto_idfp4'] == crypto_idfp
    assert db['flatland/cts100record/time4'] == time


def test_save(example_data, fs):
    db = XonoticDB(example_data)
    db['test_key'] = 'test_value'
    db.save('new.db')
    new_db = XonoticDB.load_path('new.db')
    assert new_db['test_key'] == 'test_value'
    new_db.save('new.db')
    assert len(os.listdir('.')) == 2
    f1, f2 = os.listdir('.')
    assert f1 != f2
    assert open(f1).read() == open(f2).read()
    os.mkdir('test.db')
    with pytest.raises(XonoticDBException) as e:
        new_db.save('test.db')
    assert ' exists and is not a file' in str(e.value)
