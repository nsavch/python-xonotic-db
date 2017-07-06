from xon_db.natural_sort import natural_sort_key


def test_natural_sort():
    assert sorted(['hello', 'hello9', 'hello10', 'world'], key=natural_sort_key) == ['hello', 'hello9', 'hello10', 'world']
