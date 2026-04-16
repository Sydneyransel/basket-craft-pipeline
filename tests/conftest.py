import pytest

from db import get_mysql_engine, get_pg_engine


@pytest.fixture(scope="session")
def mysql_engine():
    return get_mysql_engine()


@pytest.fixture(scope="session")
def pg_engine():
    return get_pg_engine()
