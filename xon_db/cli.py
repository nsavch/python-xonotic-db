import click

from xon_db.natural_sort import natural_sort_key
from . import XonoticDB


@click.group()
def cli():
    pass


@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
@click.argument('pattern', default='*')
def dump(file_name, pattern):
    db = XonoticDB.load_path(file_name)
    items = sorted(db.filter(pattern), key=lambda x: natural_sort_key(x[0]))
    for k, v in items:
        print('%s: %s' % (k, v))
