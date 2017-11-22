import click
import sys

from xon_db.natural_sort import natural_sort_key
from . import XonoticDB


@click.group()
@click.help_option()
@click.version_option()
def cli():
    pass


@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
@click.argument('pattern', default='*')
def dump(file_name, pattern):
    """
    Print all keys and values where key matches PATTERN. Default pattern is * (all keys)
    """
    db = XonoticDB.load_path(file_name)
    items = sorted(db.filter(pattern), key=lambda x: natural_sort_key(x[0]))
    for k, v in items:
        click.echo('%s: %s' % (k, v))


@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
@click.argument('key')
def get(file_name, key):
    """
    Print a value for the specified key. If key is not found xon_db exists with code 1.
    """
    db = XonoticDB.load_path(file_name)
    value = db.get(key)
    if value is None:
        sys.exit(1)
    else:
        click.echo(value)


@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
@click.argument('key')
@click.argument('value')
@click.option('--new', type=bool, is_flag=True, help='If the key is not found in the database, create a new record')
def set(file_name, key, value, new):
    """
    Set a new value for the specified key.
    """
    db = XonoticDB.load_path(file_name)
    if key not in db and not new:
        click.echo('Key %s is not found in the database' % key, file=sys.stderr)
        sys.exit(1)
    else:
        db[key] = value
        db.save(file_name)


@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
@click.argument('map')
@click.argument('position', type=int)
def remove_cts_record(file_name, map, position):
    """
    Remove cts record on MAP and POSITION
    """
    db = XonoticDB.load_path(file_name)
    db.remove_cts_record(map, position)
    db.save(file_name)


@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
@click.argument('crypto_idfp')
def remove_all_cts_records_by(file_name, crypto_idfp):
    """
    Remove all cts records set by player with CRYPTO_IDFP
    """
    db = XonoticDB.load_path(file_name)
    db.remove_all_cts_records_by(crypto_idfp)
    db.save(file_name)


@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
@click.argument('crypto_idfp', nargs=1)
@click.argument('crypto_idfps', nargs=-1)
def merge_cts_records(file_name, crypto_idfp, crypto_idfps):
    """
    Merge cts records made by CRYPTO_IDFPS to CRYPTO_IDFP
    """
    db = XonoticDB.load_path(file_name)
    db.merge_cts_records(crypto_idfp, crypto_idfps)
    db.save(file_name)