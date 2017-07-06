import pytest
from click.testing import CliRunner


@pytest.fixture()
def example_data():
    """
    Provides an example xonotic database
    """
    with open('tests/example.db') as f:
        return f.read()


@pytest.fixture()
def cli_runner():
    """
    Provides click runner object
    """
    return CliRunner()
