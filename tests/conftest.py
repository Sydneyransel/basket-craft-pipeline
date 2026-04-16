import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


@pytest.fixture(scope="session")
def mysql_engine():
    url = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
        f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', '3306')}"
        f"/{os.getenv('MYSQL_DATABASE')}"
    )
    return create_engine(url)


@pytest.fixture(scope="session")
def pg_engine():
    url = (
        f"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5433')}"
        f"/{os.getenv('PG_DATABASE')}"
    )
    return create_engine(url)
