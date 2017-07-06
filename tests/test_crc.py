from xon_db.crc import crc_block


def test_crc():
    assert crc_block('hello') == 53870
