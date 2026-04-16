import os
import sys
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

TABLES = ["orders", "order_items", "products"]


def get_mysql_engine():
    url = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
        f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', '3306')}"
        f"/{os.getenv('MYSQL_DATABASE')}"
    )
    return create_engine(url)


def get_pg_engine():
    url = (
        f"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5433')}"
        f"/{os.getenv('PG_DATABASE')}"
    )
    return create_engine(url)


def main():
    try:
        mysql_engine = get_mysql_engine()
        pg_engine = get_pg_engine()

        with pg_engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
            conn.commit()
        print("Raw schema ready.")

        for table in TABLES:
            with mysql_engine.connect() as conn:
                df = pd.read_sql(f"SELECT * FROM {table}", conn)
            df.to_sql(table, pg_engine, schema="raw", if_exists="replace", index=False)
            print(f"  {table}: {len(df)} rows loaded")

        print("Extraction complete.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
